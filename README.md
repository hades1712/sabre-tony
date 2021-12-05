# 备份并清理ES日志
## 修改配置文件 app-config.yml

| 意思 | 配置名 |
| ---- | --- |
| AWS的账号 | account |
| 参照ES控制台的VPC面板 | vpc_id |
| 参照ES控制台的VPC面板下选择EKS集群的安全组 | security_group_id |
| 存放SNAPSHOT的S3名字 | bucket-name |
| ES存放SNAPSHOT的名字(实际snapshot的存储还是在s3里) | es_repo_name |
| 参照ES控制台 | ES_ENDPOINT |
| 应用实际的索引前缀 | ES_INDEX_PREFIX |
| SNAPSHOT存放天数 | snapshot_retention | 
| INDEX的存放天数，到期后会生成SNAPSHOT备份 | index_retention |

## 初始化安装环境
1. mkdir es2s3 && cd es2s3
2. cdk init --language python
3. 将repo里的所有文件覆盖到当前目录下
4. 激活虚拟环境
	以下指令适用于windows，其他OS参考 https://cdkworkshop.com/30-python/20-create-project/100-cdk-init.html ）
.env\Scripts\activate.bat
5. 安装依赖
```
pip install -r requirements.txt
pip install requests -t ./lambda
pip install requests_aws4auth -t ./lambda
pip install pyyaml
```

6. 部署CDK
```
cdk synth
cdk diff
cdk bootstrap aws://630216610805/us-west-2
cdk deploy
```

7. 创建ES REPO
进入AWS控制台的Lambda页面，选择registerrepo函数
点击右上角测试，使用默认的模板直接创建新测试事件，然后点击测试
进入KIBANA页面，选择左边的devtool入口，在Console里输入 
```GET _snapshot/_all```
显示刚刚创建成功的es repo

8. 配置定时创建快照清理日志任务
进入AWS控制台的Lambda页面，选择 ManageIndices 函数
选择“添加触发器”，触发器类型选择“CloudWatch Events"
在“计划表达式”里填写 
```cron(0 5 * * ? *) ```
表示每天UTC时间5点，即北京时间13点执行该函数

9. 查看定时任务运行日志
进入AWS控制台的CloudWatch页面，选择左边的“日志组”入口
选择对应lambda函数的日志组，查看运行日志

# Thanos 方案
一组通过跨集群联合、跨集群无限存储和全局查询为Prometheus增加高可用性的组件。Improbable部署了一个大型的Prometheus来监控他们的几十个Kubernetes集群。默认的Prometheus设置在查询历史数据、通过单个API调用进行跨分布式Prometheus服务器查询以及合并多个Prometheus数据方面存在困难。

Thanos通过使用后端的对象存储来解决数据保留问题。Prometheus在将数据写入磁盘时，边车的StoreAPI组件会检测到，并将数据上传到对象存储器中。Store组件还可以作为一个基于gossip协议的检索代理，让Querier组件与它进行通信以获取数据。

Thanos还提供了时间序列数据的压缩和降采样（downsample）存储。Prometheus提供了一个内置的压缩​​模型，现有较小的数据块被重写为较大的数据块，并进行结构重组以提高查询性能。Thanos在Compactor组件（作为批次作业运行）中使用了相同的机制，并压缩对象存储数据。Płotka说，Compactor也对数据进行降采样，“目前降采样时间间隔不可配置，不过我们选择了一些合理的时间间隔——5分钟和1小时”。压缩也是其他时间序列数据库（如InfluxDB和OpenTSDB）的常见功能。

Thanos通过一种简单的可无缝接入当前系统的方案解决这些问题。其主要功能点通过Sidecar、Querier、Store和Compactor来实现，这里做一个简单介绍。

Sidecar
Sidecar作为一个单独的进程和已有的Prometheus实例运行在一个server上，互不影响。Sidecar可以视为一个Proxy组件，所有对Prometheus的访问都通过Sidecar来代理进行。通过Sidecar还可以将采集到的数据直接备份到云端对象存储服务器。「会消耗原有实例所在集群的资源，上线前可以先把原有server机器升配下」

Querier
所有的Sidecar与Querier直连，同时Querier实现了一套Prometheus官方的HTTP API从而保证对外提供与Prometheus一致的数据源接口，Grafana可以通过同一个查询接口请求不同集群的数据，Querier负责找到对应的集群并通过Sidecar获取数据。Querier本身也是水平可扩展的，因而可以实现高可部署，而且Querier可以实现对高可部署的Prometheus的数据进行合并从而保证多次查询结果的一致性，从而解决全局视图和高可用的问题。「配合云的AutoScaling」

Store
Store实现了一套和Sidecar完全一致的API提供给Querier用于查询Sidecar备份到云端对象存储的数据。因为Sidecar在完成数据备份后，Prometheus会清理掉本地数据保证本地空间可用。所以当监控人员需要调取历史数据时只能去对象存储空间获取，而Store就提供了这样一个接口。Store Gateway只会缓存对象存储的基本信息，例如存储块的索引，从而保证实现快速查询的同时占用较少本地空间。

Comactor
Compactor主要用于对采集到的数据进行压缩，实现将数据存储至对象存储时节省空间。

本次使用Thanos 与S3对接，降低Prometheus的成本，如下图架构：

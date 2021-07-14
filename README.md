# Quickstart

## Description:

`f5-agent-auditor` 主要用于检查审计 `f5-openstack-agent` 在 `Neutron DB` 中创建的资源和其下发到 BigIP 上的资源是否一致。

检查资源的范围包含：

* `BigIP partiton (Openstack project)`
* `BigIP vip (Openstack loadbalancer)`
* `BigIP vs (Openstack listener)`
* `BigIP pool (Openstack pool)`
* `BigIP pool mebmer (Openstack pool member)`

检查级别：

每次检查 `f5-agent-auditor` 需要指定 `agent id` （`--f5-agent`）作为命令参数，`f5-agent-auditor` 会检查 `agent id` 指定的 agent 在 BigIP 上创建的所有资源。通常情况下一个 `agent id` 对应一个 Neutron LBaaS 的 `service provider`，也可以理解为`f5-agent-auditor` 会检查 `agent id` 指定的 `service provider` 创建的所有资源。

## Installation

安装方式主要提供从原码安装和使用 `pip` 命令从 `PYPI`库安装。

### Install by source code

```bash
# 从 github 上下载原码
git clone https://github.com/f5devcentral/f5-agent-auditor.git -b master

# 转到源码目录下
cd f5-agent-auditor
# 使用 pip 安装
sudo pip install ./
# 或者 setup.py 安装，任意一种即可。
sudo python setup.py install
```

## Install from PYPI repository

```bash
# 直接从 PYPI 仓库安装
[stack@neutron-server-1 ~]$ sudo pip install f5-agent-auditor
```

**以上安装方式使用任意一种即可**

## Uninstallation

卸载可以直接使用 `pip`命令卸载

```bash
# 卸载 f5-agent-auditor
[stack@neutron-server-1 ~]$ sudo pip uninstall f5-agent-auditor
Uninstalling f5-agent-auditor-0.0.0:
  /usr/bin/f5-agent-auditor
  /usr/lib/python2.7/site-packages/f5-agent-auditor.egg-link
Proceed (y/n)? y
  Successfully uninstalled f5-agent-auditor-0.0.0
```

## Execution

安装后，命令 `f5-agent-auditor` 会被安装到系统中.

```bash
# 运行如下命令。
f5-agent-auditor --config-file /etc/neutron/services/f5/f5-openstack-agent-CORE.ini --config-file /etc/neutron/neutron.conf --f5-agent 1b4e247d-6c79-4d38-949f-91af99b10b2c
```
1. **`--f5-agent：`**指定需要检查审计的 `F5 LBaaS Agent UUID`, Openstack admin 用户可以使用 `neutron agent-list` 查看。
2. **`--config-file：`**需要指定两个 file，
   1. 一个是 neutron-server 的 `neutron.conf` 配置文件。
   2. 一个是选取的 F5 LBaaS Agent 使用的 `f5-openstack-agent.ini` 配置文件（比如 `f5-openstack-agent-CORE.ini`）。

```bash
# 将 neutron.conf debug 配置修改为 False，程序运行时可以输出比较简洁的 log，如下：

[stack@neutron-server-1 f5-agent-auditor]$ f5-agent-auditor --config-file /etc/neutron/services/f5/f5-openstack-agent-CORE.ini --config-file /etc/neutron/neutron.conf --f5-agent 1b4e247d-6c79-4d38-949f-91af99b10b2c
INFO f5_agent_auditor.collector.lbaas_collector [-] Get projects of agent : 1b4e247d-6c79-4d38-949f-91af99b10b2c in Neutron DB
INFO f5_agent_auditor.collector.lbaas_collector [-] get_projects_on_device takes 0.000581026077271 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get projects on device 10.145.67.245
INFO f5_agent_auditor.collector.bigip_collector [-] get_projects_on_device takes 0.0221989154816 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get loadbalancers of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_loadbalancers takes 0.000296115875244 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get loadbalancers of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_loadbalancers takes 0.000241994857788 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get loadbalancers of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_loadbalancers takes 0.0236790180206 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get loadbalancers of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_loadbalancers takes 0.0187258720398 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get listeners of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_listeners takes 0.00666093826294 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get listeners of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_listeners takes 0.00414395332336 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get listeners of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_listeners takes 0.0253779888153 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get listeners of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_listeners takes 0.0208730697632 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] Set pool members of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000219106674194 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] set_project_pool_members takes 0.0171270370483 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.0379309654236 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] Set pool members of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000220060348511 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] set_project_pool_members takes 0.00769901275635 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.0190608501434 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0208911895752 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0172410011292 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000191926956177 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000253915786743 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0212268829346 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0178661346436 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get projects on device 10.145.75.98
INFO f5_agent_auditor.collector.bigip_collector [-] get_projects_on_device takes 0.0180327892303 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get loadbalancers of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_loadbalancers takes 0.000180959701538 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get loadbalancers of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_loadbalancers takes 0.000140905380249 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get loadbalancers of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_loadbalancers takes 0.0210061073303 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get loadbalancers of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_loadbalancers takes 0.0160021781921 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get listeners of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_listeners takes 0.000160932540894 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get listeners of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_listeners takes 0.000134944915771 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get listeners of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_listeners takes 0.0203671455383 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get listeners of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_listeners takes 0.0223190784454 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000166177749634 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000140905380249 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0195679664612 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0202949047089 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000195026397705 seconds
INFO f5_agent_auditor.collector.lbaas_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.lbaas_collector [-] get_project_pools takes 0.000169992446899 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 346052548d924ee095b3c2a4f05244ac
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0196969509125 seconds
INFO f5_agent_auditor.collector.bigip_collector [-] Get pools of project: 57e89acdfb6e40a2bc7f6185645dbbdd
INFO f5_agent_auditor.collector.bigip_collector [-] get_project_pools takes 0.0193870067596 seconds
INFO f5_agent_auditor.auditor [-] main takes 0.994650840759 seconds
```

## Evaluation

如果一个 F5 LBaaS Agent 控制多个 BigIP 机器（比如 HA 一对 BigIP 设备），且 Neutron DB 中有些数据在某些 BigIP 检查不到，那么 `f5-agent-auditor` 程序运行完后，会在 Linux OS 的 `/tmp` 目录下产生 `<bigip_hostname>.csv` 文件，记录丢失的 resource 和其状态。如下：

```bash
# 文件名称如下：
# /tmp/check_10.145.67.245.csv
# /tmp/check_10.145.75.98.csv

[stack@neutron-server-1 f5-agent-auditor]$ cat /tmp/check_10.145.67.245.csv
resource type,uuid,provisioning status,project id,pool id,detail
loadbalancer,4a7ebe71-a13b-4257-bc3f-c67bba87bbb8,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
loadbalancer,76038dff-4438-4afa-9068-9c5905db8582,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
loadbalancer,36638069-1c7b-4a33-9fe5-5238f947793d,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
listener,8477ba31-0c52-477b-aba0-99babdb3f3c1,ERROR,346052548d924ee095b3c2a4f05244ac,,
listener,b015d913-c996-443f-b332-33146514341e,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
listener,9b0f0962-6455-43e0-86ee-50800d392243,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
pool,7640844c-115c-4145-869c-7e88d5b14c70,ACTIVE,57e89acdfb6e40a2bc7f6185645dbbdd,,
pool,061408d4-3d57-4317-8b35-8ee2eb3d2f18,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
pool,a32cf197-aef2-4c04-86ac-2f4fae825a79,ACTIVE,57e89acdfb6e40a2bc7f6185645dbbdd,,
pool,8755a316-b066-4194-b31c-91fec94c7d47,ACTIVE,346052548d924ee095b3c2a4f05244ac,,
member,856204a3-44aa-4669-929f-2104a0fc5124,ACTIVE,57e89acdfb6e40a2bc7f6185645dbbdd,7640844c-115c-4145-869c-7e88d5b14c70,"{'port': u'123', 'address': u'192.168.2.123'}"
member,ec27fb36-daec-4f96-beb8-b4fb50d5f0f4,ACTIVE,346052548d924ee095b3c2a4f05244ac,8755a316-b066-4194-b31c-91fec94c7d47,"{'port': u'124', 'address': u'172.168.2.124'}"
member,f157fcb0-77b2-47e4-9870-bb6574eba252,ACTIVE,346052548d924ee095b3c2a4f05244ac,8755a316-b066-4194-b31c-91fec94c7d47,"{'port': u'125', 'address': u'172.168.2.125'}"
member,0cb89299-4d18-4e18-bd77-ee4e2fedf166,ACTIVE,346052548d924ee095b3c2a4f05244ac,061408d4-3d57-4317-8b35-8ee2eb3d2f18,"{'port': u'123', 'address': u'172.168.1.213'}"
```

`<bigip_hostname>.csv` 文件可以通过 `Execel` 打开查看，做后续整理。

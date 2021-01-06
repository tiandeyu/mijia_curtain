## 杜亚M1 home assistant 插件


> dooya_curtain是一款ha自定义插件, 通过miot协议接入到homeassistant  
> 不需要额外改造任何硬件，通过WIFI，米家-HA双平台接入  
> 现已经实现开合帘、设置开合位置、状态监控等功能  
  
### 支持型号 model  
 获取token的时候顺便获得  
 
| 名称 | 型号 | 
| :---- | :--- | 
| 杜亚M1 | dooya.curtain.m1 | 
| 杜亚M2 | dooya.curtain.m2 | 
| 情景开合电机WIFI X版（闲鱼米家电机） | babai.curtain.bb82mj | 
| 绿米窗帘电机WIFI版 | lumi.curtain.hagl05 | 


### 下载custom component
下载下面网址所有文件到如下目录/config/custom_components/
https://github.com/tiandeyu/dooya_curtain/tree/main/custom_components

```shell
//文件目录结构如下
/config/custom_components/dooya_curtain/__init__.py
/config/custom_components/dooya_curtain/cover.py
/config/custom_components/dooya_curtain/manifest.json
```

### configuration.yaml配置 
| 名称 | 可选 | 描述 |
| :---- | :---: | ----- |
| name | 否 | ha中显示传感器的名字 |
| host | 否 | 窗帘电机IP地址，需要在路由器设为固定IP |
| token | 否 | 米家设备token |
| model | 否 | 设备型号 |
| scan_interval | 是 | 刷新间隔s，默认30 |

 
```yaml
cover:
  - platform: dooya_curtain
    name: 'Bedroom Cover'
    host: 192.168.2.79
    token: d863582422bc743e4ac30d91fe037373
    model: dooya.curtain.m1
    scan_interval: 10
```

### 米家token获取
```url
https://github.com/tiandeyu/Xiaomi-cloud-tokens-extractor
```


## 米家平台窗帘 home assistant 插件


> mijia_curtain是一款ha自定义插件, 通过miot协议接入到homeassistant
> 
> 支持开合帘、设置开合位置、状态监控等功能  
  
### 支持型号，米家平台所有开启MIoT协议的窗帘

### 下载custom component
下载下面网址所有文件到如下目录/config/custom_components/
https://github.com/tiandeyu/mijia_curtain/tree/main/custom_components

```shell
//文件目录结构如下
/config/custom_components/mijia_curtain/__init__.py
/config/custom_components/mijia_curtain/cover.py
/config/custom_components/mijia_curtain/manifest.json
```

### configuration.yaml配置 
| 名称 | 可选 | 描述 |
| :---- | :---: | ----- |
| name | 否 | ha中显示传感器的名字 |
| host | 否 | 窗帘电机IP地址，需要在路由器设为固定IP |
| token | 否 | 米家设备token |
| model | 是 | 设备型号(非必填，如果没填会自动拉取，HA需要有外网) |
| scan_interval | 是 | 刷新间隔s，默认30 |

 
```yaml
cover:
  - platform: mijia_curtain
    name: 'Bedroom Cover'
    host: 192.168.2.79
    token: d863582422bc743e4ac30d91fe037373
    # model: dooya.curtain.m1
    # scan_interval: 10
```

### 米家token获取
```url
https://github.com/tiandeyu/Xiaomi-cloud-tokens-extractor
```

### 已验证型号 model   

> 如果ha环境没有外网可以手工填写model配置，仅支持以下几个型号   
> 未验证型号直接填写token，会自动从网络拉取model配置

| 名称 | 型号 | 
| :---- | :--- | 
| 杜亚M1 | dooya.curtain.m1 | 
| 杜亚M2 | dooya.curtain.m2 | 
| 情景开合电机WIFI X版（闲鱼米家电机） | babai.curtain.bb82mj | 
| 绿米窗帘电机WIFI版 | lumi.curtain.hagl05 |
| 绿米窗帘电机WIFI版 | lumi.curtain.hmcn01 |

### 不支持型号

| 名称 | 型号 | 
| :---- | :--- | 
| 邦先生智能晾衣机-简约款 | mrbond.airer.m1tpro | 

## 杜亚米家窗帘电机


>duya_mijia_cover是一款ha自定义插件,通过miot协议接入到homeassistant
>现已经实现开合帘、设置开合位置、状态监控等功能


### 下载custom component
下载下面网址所有文件到如下目录/config/custom_components/
https://github.com/tiandeyu/duya_mijia_cover/tree/main/custom_components

```shell
//文件目录结构如下
/config/custom_components/duya_mijia_cover/__init__.py
/config/custom_components/duya_mijia_cover/binary_sensor.py
/config/custom_components/duya_mijia_cover/manifest.json
```

### configuration.yaml配置 
| 名称 | 可选 | 描述 |
| :---- | :---: | ----- |
| name | 否 | ha中显示传感器的名字 |
| host | 否 | 窗帘电机IP地址，需要在路由器设为固定IP |
| token | 否 | 米家设备token |
| scan_interval | 是 | 刷新间隔s，默认30 |
 
```yaml
cover:
  - platform: duya_mijia_cover
    name: 'Bedroom Cover'
    host: 192.168.2.79
    token: d863582422bc743e4ac30d91fe037373
    scan_interval: 10



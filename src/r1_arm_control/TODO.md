# r1_arm_control TODO

## 已完成

- [x] 建立 `r1_arm_control` package
- [x] 实现升降电机 controller，默认 Motor 5
- [x] 实现水平移动电机 controller，默认 Motor 6
- [x] 实现夹爪电机 controller，默认 Motor 7
- [x] 实现 L2/R2 控制升降
- [x] 实现 D-pad 控制水平移动和速度档位
- [x] 实现 L1/R1 控制夹爪
- [x] Motor 7 支持 0.5s 两段式速度及 START/SELECT 高速档调节
- [x] 三个 controller 均实现 `timeout_sec` 安全归零
- [x] 新增 README，记录 topic、参数、timeout 行为和启动方式

## 待完成

- [ ] 将三个 controller 的重复安全逻辑抽成 package 内部 helper，减少重复代码
- [ ] 为 controller 增加 launch 文件和 YAML 参数文件
- [ ] 为 joystick bridge 增加可配置按键映射
- [ ] 增加无硬件 topic 级测试
- [ ] 根据真实机械限位加入软限位或 limit switch 输入

> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# operation_mode_control TODO

## 2026-06-19 初始版本

- [x] 新增 `operation_mode_control` package
- [x] 新增 `operation_mode_selector_node`
- [x] 發布 `/operation_mode`：`0=INVALID, 1=STAFF, 2=KFS`
- [x] SELECT / 中左直接切 STAFF mode
- [x] START / 中右直接切 KFS mode
- [x] joystick timeout 後發布 INVALID
- [x] 新增無硬件單元測試
- [ ] 實機確認 SELECT/START 對應中左/中右鍵
- [ ] 實機確認 mode 切換不會自動觸發任何機構動作


## 2026-06-19 mode 操作策略

- [x] 確認 `SELECT=STAFF`、`START=KFS`
- [x] Zone3 不新增第三套鍵位，由機手手動切 STAFF/KFS mode
- [x] 文件補充 mode 不直接控制 actuator，只作為下游 bridge gate

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07

echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_min_interval
echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_max_interval
setcap cap_net_raw+ep `which hcitool`

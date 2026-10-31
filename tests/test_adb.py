from unmeta.adb import (
    classify_connect,
    parse_devices,
    parse_ip_addr,
    parse_ip_route,
    parse_wm_size,
)

DEVICES = """\
* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
2G0YC1ZF8B0123     device usb:1-1 product:eureka model:Quest_3 device:eureka transport_id:3
1WMHH000000000     unauthorized usb:1-2 transport_id:4
192.168.1.80:5555  device product:eureka model:Quest_3 device:eureka transport_id:5
ABC123             no permissions (missing udev rules? user is in the plugdev group); see [http://developer.android.com/tools/device.html] usb:1-3
emulator-5554      offline
"""


def test_parse_devices():
    devices = parse_devices(DEVICES)
    assert [(d.serial, d.state) for d in devices] == [
        ("2G0YC1ZF8B0123", "device"),
        ("1WMHH000000000", "unauthorized"),
        ("192.168.1.80:5555", "device"),
        ("ABC123", "no permissions"),
        ("emulator-5554", "offline"),
    ]
    assert devices[0].model == "Quest 3"
    assert [d.is_usb for d in devices] == [True, True, False, True, False]


def test_parse_ip_addr():
    out = """\
30: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 3000
    inet 192.168.1.80/24 brd 192.168.1.255 scope global wlan0
       valid_lft forever preferred_lft forever
"""
    assert parse_ip_addr(out) == "192.168.1.80"
    assert parse_ip_addr('Device "wlan0" does not exist.') is None


def test_parse_ip_route_prefers_wifi():
    out = """\
10.0.0.0/8 dev rmnet0 proto kernel scope link src 10.1.2.3
192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.80
"""
    assert parse_ip_route(out) == "192.168.1.80"


def test_classify_connect():
    assert classify_connect("connected to 192.168.1.80:5555") == "ok"
    assert classify_connect("already connected to 192.168.1.80:5555") == "ok"
    assert classify_connect("failed to authenticate to 192.168.1.80:5555") == "unauthorized"
    assert (
        classify_connect("cannot connect to 192.168.1.80:5555: No connection could be made (10061)")
        == "unreachable"
    )
    assert classify_connect("failed to connect to '192.168.1.80:5555': Connection refused") == (
        "unreachable"
    )


def test_parse_wm_size():
    assert parse_wm_size("Physical size: 3840x2160") == (3840, 2160)
    assert parse_wm_size("Physical size: 3840x2160\nOverride size: 1920x1080") == (1920, 1080)
    assert parse_wm_size("error: device offline") is None

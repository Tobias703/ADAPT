graph [
    node [
        id 0
        label "censored"
        host_bandwidth_down "100 Mbit"
        host_bandwidth_up "100 Mbit"
    ]
    node [
        id 1
        label "bridge"
        host_bandwidth_down "100 Mbit"
        host_bandwidth_up "100 Mbit"
    ]
    node [
        id 2
        label "free"
        host_bandwidth_down "100 Mbit"
        host_bandwidth_up "100 Mbit"
    ]

    edge [
        source 0
        target 1
        latency "10 ms"
        packet_loss 0.0
    ]
    edge [
        source 1
        target 2
        latency "10 ms"
        packet_loss 0.0
    ]

    edge [
        source 0
        target 2
        latency "1 ms"
        packet_loss 1.0
    ]
    
    edge [
        source 0
        target 0
        latency "10 ms"
        packet_loss 0.0
    ]
    edge [
        source 1
        target 1
        latency "10 ms"
        packet_loss 0.0
    ]
    edge [
        source 2
        target 2
        latency "10 ms"
        packet_loss 0.0
    ]
]

# Distributed System Lab 3: Monitor Integration with etcd

This guide outlines the steps to deploy a distributed monitoring system using etcd for configuration storage and state management (heartbeat), running on Kubernetes and Python.


## 1. Prerequisites
- **OS:** Windows (WSL2 - Ubuntu) / Linux / macOS
- **Kubernetes:** Docker Desktop hoặc Minikube
- **Python:** 3.x
- **Tools:** kubectl, pip, skaffold

---

## 2. Project Structure
```
lab3/
├── etcd.yaml           # Kubernetes deployment file (storageClassName fixed)
├── server_manager.py   # Server-side code (manages config, watches heartbeats)
├── node_agent.py       # Node-side code (sends heartbeats, watches config)
├── requirements.txt    # Python dependencies list
└── README.md           # Instructions
```


## 3. Environment Setup

### 3.1 Deploy etcd on Kubernetes

#### Option 1: Using kubectl (classic)
- Make sure the `storageClassName: local-path` line in `etcd.yaml` is **removed or commented out** to avoid "Pending" errors on standard clusters.
- Deploy etcd:
  ```sh
  kubectl apply -f etcd.yaml
  ```
- Wait for the Pod to reach Running status:
  ```sh
  kubectl get pods -n etcd -w
  ```

#### Option 2: Using Skaffold (recommended for local development)
- Make sure the `storageClassName: local-path` line in `etcd.yaml` is **removed or commented out** to avoid "Pending" errors on standard clusters.
- Deploy etcd with skaffold:
  ```sh
  skaffold dev
  ```
  or if you want to apply only once:
  ```sh
  skaffold run
  ```
- To check Pod status:
  ```sh
  kubectl get pods -n etcd -w
  ```

### 3.2 Install Python Libraries
Due to compatibility issues between the older etcd3 library and newer protobuf versions, specific versions must be installed in a virtual environment.

- Create and activate a virtual environment (venv):
  ```sh
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install Dependencies:
  Create a `requirements.txt` file with the following content:
  ```text
  etcd3==0.12.0
  protobuf==3.20.3
  tenacity==8.2.3
  ```
  Then run:
  ```sh
  pip install -r requirements.txt
  ```


## 4. Execution Guide
The system requires **3 separate Terminal windows** to run simultaneously. Open 3 WSL/Terminal windows.

### 🖥️ Terminal 1: Port Forwarding (Bridge)
Thiết lập kết nối từ máy local (WSL) tới Pod etcd trong Kubernetes.

> venv **không cần thiết** ở bước này
```sh
kubectl port-forward -n etcd pod/etcd-0 2379:2379
```
**Lưu ý:** Giữ terminal này luôn mở. Nếu gặp lỗi "Connection refused" ở các bước sau, hãy kiểm tra lại lệnh này.

### 🖥️ Terminal 2: Server Manager
Runs the Server to monitor nodes and push configurations.
```sh
cd /path/to/lab3
source venv/bin/activate  # venv activation is mandatory
python server_manager.py
```
Expected output:
```
Server started. Watching heartbeats...
```

### 🖥️ Terminal 3: Node Agent
Simulates a client node sending "alive" signals.
```sh
cd /path/to/lab3
source venv/bin/activate  # venv activation is mandatory
python node_agent.py
```
Expected output:
```
[Heartbeat] Sent for ...
```


## 5. Demo Scenario
Follow these steps to demonstrate that the system meets the Lab requirements:

### Check Heartbeat
When Terminal 3 (Node) is started, Terminal 2 (Server) should log:
```
[+] Node <hostname> is ALIVE
```

### Dynamic Configuration Update
In Terminal 2 (Server), enter the update command:
```
update <your-node-hostname> 2
```
(Example: `update LAPTOP-UMVK4LFU 2` — Get the hostname from the heartbeat log.)

Check Terminal 3 (Node): The node should immediately receive the update event and print:
```
[Config] Detected update...
[Config] Updated successfully...
```
(The loop interval will decrease to 2 seconds.)

### Failure Detection (Node Crash)
In Terminal 3, press `Ctrl + C` to kill the Node agent.
Wait for about 5-6 seconds (TTL expiration).
Check Terminal 2, the Server should report:
```
[-] Node <hostname> is DEAD (TTL expired)
```


### Error: Pod etcd-0 stuck in Pending
- **Cause:** Invalid `storageClassName` in the YAML file.
- **Fix:** Remove the `storageClassName: local-path` line from `etcd.yaml`, then delete the old statefulset and re-apply (with kubectl or skaffold).
- **Cause:** You are trying to run a system command or python without the virtual environment active, or the environment is corrupted.
- **Fix:** Run `source venv/bin/activate` again.

### Error: `Connection refused`
- **Cause:** Terminal 1 (Port Forward) is closed or not running.
- **Fix:** Run the `kubectl port-forward` command again.

### Error: `TypeError: Descriptors cannot be created directly`
- **Cause:** protobuf version is too new (4.x or 5.x).
- **Fix:** Run `pip install protobuf==3.20.3`.

### Error: Pod etcd-0 stuck in Pending
- **Cause:** Invalid `storageClassName` in the YAML file.
- **Fix:** Remove the `storageClassName: local-path` line from `etcd.yaml`, then delete the old statefulset and re-apply.

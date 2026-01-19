# Docker Mastery Quiz

Test your understanding of the complex architecture we just built.

### Question 1: Network Isolation
In our `docker-compose.yml`, the **Vote Service** is connected to `frontend-net` and `backend-net`. The **Database** is on `db-net`.
**Scenario**: A hacker compromises the **Vote Service** container.
**Question**: Can they directly access the Database to steal data? Why or why not?

<details>
<summary>Click for Answer</summary>
**No.** The Vote Service and Database do not share a common network. The Vote Service is on `frontend-net` and `backend-net`, while the Database is only on `db-net`. The only bridge between them is the **Worker** (or Result) service. The hacker would need to pivot through the Worker or Result service first.
</details>

---

### Question 2: Multistage Builds & Layer Caching
Look at the `vote/Dockerfile`. We copy `requirements.txt` and run `pip install` *before* copying `.` (the rest of the code).
**Question**: If you change a line of code in `app.py` and rebuild, will Docker re-run `pip install`? Explain your answer.

<details>
<summary>Click for Answer</summary>
**No.** Docker uses layer caching. Since `requirements.txt` hasn't changed, the hash of that COPY instruction remains the same. Docker sees that the subsequent RUN instruction (pip install) matches the cache, so it reuses the cached layer. It only invalidates the cache starting at `COPY . .` because the source files changed. This makes builds much faster.
</details>

---

### Question 3: Data Persistence
**Scenario**: You run `docker-compose down` and then `docker-compose up`. The vote counts are still there.
**Question**: If you wanted to completely wipe the data and start fresh, what exact command would you run, and which line in `docker-compose.yml` is responsible for this persistence?

<details>
<summary>Click for Answer</summary>
**Command**: `docker-compose down -v` (or `--volumes`).
**Reason**: The line `volumes: - db-data:/var/lib/postgresql/data` in the `db` service definition tells Docker to store the database files in a named volume (`db-data`). `docker-compose down` removes containers but leaves volumes by default. Adding `-v` forces the removal of the volume.
</details>

---

### Question 4: The "Depends On" Trap
**Scenario**: In `docker-compose.yml`, the `worker` service has `depends_on: - db`.
**Question**: Does this guarantee that the Database is ready to accept connections when the Worker starts?

<details>
<summary>Click for Answer</summary>
**No.** `depends_on` only waits for the container to *start* (enter the running state). It does not wait for the application inside (Postgres) to be ready to accept TCP connections. This is why our `worker/main.py` includes a retry loop (or why we use `healthcheck` in compose to be safer, though `depends_on` condition `service_healthy` is the strict way to enforce it).
</details>

---

### Question 5: Build Context
**Scenario**: You are in the root directory and run `docker build -t my-app ./vote`. Inside `vote/Dockerfile`, you have `COPY ../docker-compose.yml .`.
**Question**: Will this build succeed or fail?

<details>
<summary>Click for Answer</summary>
**Fail.** Docker builds cannot access files outside the **build context**. Since you specified `./vote` as the context, the Docker daemon only receives files inside that folder. It cannot "see" the parent directory to copy `docker-compose.yml`.
</details>

---

### Question 6: The "ENV PATH" Mystery
**Code**: `ENV PATH=/root/.local/bin:$PATH`
**Question**: In our multi-stage build, we install pip packages with `--user` in the builder stage. What catastrophic failure happens at runtime if we delete this `ENV` line?

<details>
<summary>Click for Answer</summary>
**Command Not Found Error.**
When using `pip install --user`, executables (like `gunicorn` or `pytest`) are installed into `~/.local/bin` (or `/root/.local/bin`), NOT the standard `/usr/bin`. By default, Linux does not check this local folder. Without adding it to `$PATH`, the final `CMD ["gunicorn", ...]` will fail because the system cannot find the `gunicorn` executable.
</details>

---

### Question 7: The "COPY --from" Magic
**Code**:
```dockerfile
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
```
**Question**: What happens if we remove these lines and just use `COPY . .` in the final stage instead?

<details>
<summary>Click for Answer</summary>
**Module Not Found Error.**
The final stage (`FROM python:3.9-slim`) starts **empty** (except for Python itself). If you remove the `COPY --from=builder`, your final image will not have any of the libraries you installed in the Builder stage (flask, redis, etc.). Your app will crash immediately with `ModuleNotFoundError: No module named 'flask'`.
</details>

---

### Question 8: Base Image Swap
**Scenario**: You change `FROM python:3.9-slim` to `FROM python:3.9-alpine` in the runtime stage to save space.
**Question**: Your app suddenly crashes with "Library not found" errors related to `psycopg2`. Why?

<details>
<summary>Click for Answer</summary>
**Missing System Dependencies.**
`alpine` is a completely different Linux distribution (musl-based vs glibc-based). Python wheels built on `slim` (Debian) often rely on system libraries (like `libpq` for Postgres) that are pre-installed or easily available in Debian but missing in Alpine. You would need to manually `apk add postgresql-libs` in Alpine to make it work.
</details>

---

### Question 9: Removing Network Definitions
**Scenario**: You decide `networks:` is too complex, so you delete the entire `networks` block at the bottom of `docker-compose.yml` and remove the `networks:` lines from every service.
**Question**: Does the app still work? And what is the security implication?

<details>
<summary>Click for Answer</summary>
**Functionality**: Yes, it likely works. Docker Compose creates a `default` network and puts everyone in it. Services can talk to each other using their service names.
**Security**: **Total Collapse.** Now `frontend` can talk directly to `db`. `vote` can talk to `db`. If a hacker compromises the Frontend, they have direct network access to brute-force your Database. You have lost your "Defense in Depth".
</details>

---

### Question 10: "COPY . ." vs "COPY . /app"
**Code**: `COPY . .` inside `WORKDIR /app`.
**Question**: What does the second dot mean? If we change it to `COPY . /src`, what happens?

<details>
<summary>Click for Answer</summary>
**Meaning**: The first `.` is the source (your computer's folder). The second `.` is the destination (the container's **current working directory**).
**Change**: If you change it to `COPY . /src`, your code lands in `/src`. However, if your `WORKDIR` is still `/app` and your `CMD` runs `python app.py`, it will fail because `app.py` is not in `/app`, it's in `/src`. You must align your COPY destination with your WORKDIR and CMD.
</details>

---

### Question 11: Nginx Proxy Ports
**Code**: `proxy_pass http://vote:80/vote;`
**Question**: Why `80`? Why not `8080` or `5000`? What happens if you change it to `8080`?

<details>
<summary>Click for Answer</summary>
**Internal Container Port.**
We configured our Python apps (Gunicorn) to listen on port `80` inside the container (`CMD ["gunicorn", "-b", "0.0.0.0:80", ...]`). Nginx is talking to the container *inside* the Docker network, so it must use that internal port.
**8080?**: That is the *external* port on your laptop. Nginx cannot see that.
**5000?**: If your Python app was listening on 5000 (standard Flask), you would use 5000. But we explicitly set it to 80.
</details>

---

### Question 12: Port Mapping Strategy
**Observation**: Only the `frontend` service has a `ports:` section (`8080:80`). The `vote`, `result`, and `db` services do not.
**Question**: Why didn't we add `ports:` to the other services?

<details>
<summary>Click for Answer</summary>
**Security & Isolation.**
By removing `ports:`, we ensure that `vote`, `result`, and `db` are **completely invisible** to the outside world (your host machine). You cannot bypass the Frontend. You cannot connect to the Database tool from your laptop. This forces all traffic to go through the controlled entry point (Nginx), which is a security best practice.
</details>

---

### Question 13: Build Targets
**Code**: `frontend` uses `target: final`, but `vote` uses `target: runtime`.
**Question**: Why are they different? Can we make them all `target: production`?

<details>
<summary>Click for Answer</summary>
**Must Match Dockerfile `AS` Alias.**
The `target` in `docker-compose.yml` simply tells Docker *which stage* in the Dockerfile to stop at.
In `frontend/Dockerfile`, we wrote `FROM nginx... AS final`.
In `vote/Dockerfile`, we wrote `FROM python... AS runtime`.
You can rename them all to `AS production` in the Dockerfiles, and then update compose to `target: production`. They just need to match.
</details>

---

### Question 14: Restart Policies
**Code**: `restart: always`
**Question**: What exactly does this do? If I stop the container manually with `docker stop`, will it restart?

<details>
<summary>Click for Answer</summary>
**Automatic Recovery.**
`restart: always` means:
1.  If the app crashes (error exit code), Docker restarts it.
2.  If you reboot your server (or restart the Docker daemon), Docker starts the container up again.
**Exception**: If you manually run `docker stop`, Docker assumes you *meant* to stop it, so it will **not** restart it until you run `docker start` or reboot the daemon.
</details>

---

### Question 15: Healthcheck "Curl" Flags
**Code**: `curl -f http://localhost:80/health`
**Question**: Why is the `-f` flag critical here? What happens if we remove it?

<details>
<summary>Click for Answer</summary>
**Fail on Server Error.**
Normally, if `curl` hits a page that returns HTTP 500 (Server Error), it still exits with code 0 (Success) because it successfully retrieved *some* content (the error page).
The `-f` flag tells curl to "fail silently" on HTTP errors (4xx or 5xx) and return a non-zero exit code (Error). Docker's Healthcheck only marks a container "Unhealthy" if the command returns an exit code != 0. Without `-f`, a broken 500-error app would still look "Healthy".
</details>

---

### Question 16: Healthcheck Timing
**Code**: `interval: 10s`, `timeout: 5s`, `retries: 3`
**Question**: Explain exactly how long it takes for a broken container to be marked "unhealthy".

<details>
<summary>Click for Answer</summary>
**~30 Seconds.**
Docker waits `10s` (interval) -> runs check -> fails (takes up to `5s` timeout) -> waits `10s` -> check -> fails -> waits `10s` -> check -> fails (3rd retry).
Only after 3 consecutive failures does the status flip to `unhealthy`. This prevents a temporary blip from killing the container immediately.
</details>

---

### Question 17: ENV vs ARG
**Question**: We used `environment:` in Compose. We didn't use `ARG` or `args:`. When would you use `ARG`?

<details>
<summary>Click for Answer</summary>
**Build Time vs Run Time.**
*   `ARG` is available **only during `docker build`**. Use it for things like software versions (`ARG PYTHON_VERSION=3.9`) or build settings. It is baked into the image.
*   `ENV` (Environment Variables) is available **when the container runs**. Use it for configuration like DB Hostnames, Passwords, API Keys. Since we need to tell the app where Redis is *at runtime* (depending on the network), `ENV` is the correct choice.
</details>

---

### Question 18: Volumes Usage
**Observation**: Only `db` has a `volumes:` section.
**Question**: Why didn't we give volumes to `vote` or `worker`?

<details>
<summary>Click for Answer</summary>
**Stateless vs Stateful.**
*   **Vote/Worker/Result**: These are **Stateless**. They process logic but don't store long-term data on their own disk (they send it to Redis/DB). If you delete the container and recreate it, nothing is lost because the code is in the Image.
*   **Database**: This is **Stateful**. If you delete the Postgres container, the data inside `/var/lib/postgresql/data` is gone forever *unless* you map it to a Volume (`db-data`). The volume exists outside the container lifecycle.
</details>

---

### Question 19: The "Root" Security Trap
**Observation**: We didn't specify a `USER` in our Dockerfiles.
**Question**: Who is running the application inside the container? Why is this a security risk, and how would you fix it?

<details>
<summary>Click for Answer</summary>
**Root.**
By default, Docker containers run as `root` (ID 0). If a hacker exploits your Python app (e.g., Code Injection), they gain **root access** inside the container. If there's a kernel vulnerability (container breakout), they could gain root on your **Host Machine**.
**Fix**: Create a non-privileged user in the Dockerfile (`RUN useradd -m appuser`) and switch to it (`USER appuser`) before the `CMD`.
</details>

---

### Question 20: Secrets Management
**Code**: `DB_PASSWORD=postgres` in `docker-compose.yml`.
**Question**: This file is committed to GitHub. Why is this a disaster for production, and what feature of Docker Compose should you use instead?

<details>
<summary>Click for Answer</summary>
**Credential Leak.**
Hardcoding passwords in plain text means anyone with access to the repo has your DB keys.
**Solution**: Use **Docker Secrets** (Swarm) or, for Compose, use an `.env` file (added to `.gitignore`) and reference it like `DB_PASSWORD=${DB_PASSWORD}`.
</details>

---

### Question 21: The "Bloated Context"
**Scenario**: You have a 2GB `.git` folder and a huge `node_modules` folder on your host. You run `docker build`. It takes forever to "Send build context to Docker daemon".
**Question**: Which file are you missing, and how does it fix this?

<details>
<summary>Click for Answer</summary>
**`.dockerignore`**.
Before building, Docker zips everything in the directory and sends it to the daemon. If you don't ignore heavy folders like `.git`, `node_modules`, or `__pycache__`, the build context is huge. A `.dockerignore` file acts like `.gitignore` to exclude these files from being sent.
</details>

---

### Question 22: Graceful Shutdown (PID 1)
**Code**: `CMD ["python", "app.py"]`
**Question**: When you run `docker stop`, does your app shut down immediately or wait 10 seconds and gets killed? Why?

<details>
<summary>Click for Answer</summary>
**It likely gets killed forceably (SIGKILL) after 10s.**
Linux signals (SIGTERM) are sent to Process ID 1 (PID 1). In a container, your app is PID 1. Standard Python often ignores SIGTERM unless you program it to handle signals.
**Fix**: Use a proper process manager like `tini` (`ENTRYPOINT ["/usr/bin/tini", "--"]`) or a server like `gunicorn` (which handles signals correctly) instead of raw `python`.
</details>

---

### Question 23: Layer Order Strategy
**Scenario**: You put `COPY . .` on line 2, and `RUN pip install ...` on line 3.
**Question**: Why will your colleagues hate you?

<details>
<summary>Click for Answer</summary>
**Slow Builds.**
Every time you change code (which happens often), line 2's cache is invalidated. This forces Docker to re-run line 3 (`pip install`) every single time. By putting `pip install` *before* `COPY . .` (and copying only requirements first), we leverage caching so we only reinstall deps when `requirements.txt` changes.
</details>

---

### Question 27: Targeting the Wrong Stage
**Scenario**: In `docker-compose.yml`, you change `target: runtime` to `target: builder` for the Worker service.
**Question**: Does the app still work? What are the 3 negative consequences?

<details>
<summary>Click for Answer</summary>
**It fails.**
1.  **No CMD**: The `builder` stage in our Dockerfile doesn't have a `CMD ["python", "main.py"]` instruction. It defaults to the base image's CMD (python interactive shell), so the container will likely start and do nothing or exit.
2.  **Tests Skipped**: The `tester` stage comes *after* `builder`. Docker stops early, so your unit tests never run.
3.  **Image Bloat**: You ship the build tools and cached files, making the image larger than the optimized `runtime` image.
</details>

---

### Question 28: Removing the Target Field
**Scenario**: You simply delete the line `target: runtime` from `docker-compose.yml`.
**Question**: Does the build fail? What does Docker do by default?

<details>
<summary>Click for Answer</summary>
**It Works (Coincidentally).**
If you don't specify a `target`, Docker builds the **entire Dockerfile** from top to bottom and uses the result of the **last stage**.
Since our last stage happens to be `AS runtime`, you get the correct image.
**Risk**: If someone edited the Dockerfile and put the `tester` stage at the bottom, your production app would suddenly be running tests instead of the app! Explicitly setting `target` is safer.
</details>

---

### Question 24: Redis Commands
**Code**: `r.rpush(...)` and `r.blpop(...)`
**Question**: What do the acronyms **RPUSH** and **BLPOP** actually stand for, and why is the "B" important for our Worker?

<details>
<summary>Click for Answer</summary>
**Definitions**:
*   **RPUSH**: **R**ight **PUSH** (Add to the tail/end).
*   **BLPOP**: **B**locking **L**eft **POP** (Remove from head/start).

**Importance of "B" (Blocking)**:
Without "Blocking", the worker would need to check the queue continuously (polling), e.g., `while True: pop()`. If the queue is empty, this loop spins 1000s of times per second, burning 100% CPU.
With **Blocking**, the worker says "Wake me up when data arrives" and sleeps, using near 0% CPU while waiting.
</details>

---

### Question 25: "Started" vs "Healthy"
**Code**:
```yaml
depends_on:
  db:
    condition: service_healthy
```
**Question**: By default, `depends_on` only waits for `service_started`. What is the critical difference between `service_started` and `service_healthy`, and why does it matter for a Database?

<details>
<summary>Click for Answer</summary>
**Process Running vs App Ready.**
*   **Service Started**: Docker checks "Did the container process launch?". For a database, the process starts immediately, but it might take 10 seconds to load files and open the port.
*   **Service Healthy**: Docker checks "Did the Healthcheck command (pg_isready) return success?". This confirms the Database is actually **accepting connections**.
If you only wait for "Started", your app will try to connect to the DB before it's ready and crash. Waiting for "Healthy" ensures the dependency is fully operational.
</details>

---

### Question 26: How Docker Detects Changes (The "Touch" Effect)
**Scenario**: You edit `app.py` (even just adding a space) and run `docker-compose up --build`.
**Question**: How does Docker know that the file changed? Does it rebuild everything from scratch? Explain the mechanism.

<details>
<summary>Click for Answer</summary>
**Checksums & Layer Caching.**
1.  **Context**: Docker calculates a SHA256 checksum (hash) for every file in your build context.
2.  **Comparison**: When it reaches `COPY . .`, it compares the current hash of your files against the hash stored in its cache from the last build.
3.  **Invalidation**: If you "touched" `app.py`, the hash changes. Docker marks the cache as **invalid** for that step.
4.  **Cascade**: It re-runs that `COPY` instruction **and every instruction after it** (like `RUN pip install` if it was below it). Steps *before* the change (like the base image or previous `COPY requirements.txt`) are still cached and skipped.
</details>

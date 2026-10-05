# fastapi-assetdb

A small FastAPI starter with automated testing and deployment to **Azure App Service (Linux)** through GitHub Actions. No database is configured yet.

## Endpoints

| Path | Purpose |
| --- | --- |
| `/` | Welcome JSON |
| `/health` | Health check: `{"status":"ok"}` |
| `/docs` | Interactive Swagger documentation |
| `/redoc` | Alternative API documentation |
| `/openapi.json` | OpenAPI schema |

## Run locally on Windows

Use Python **3.12**, matching the workflow and Azure runtime. If your existing `.venv` uses an older Python version, remove or rename it and recreate it after installing Python 3.12. From the repository directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. Stop the server with Ctrl+C.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

On Linux/macOS, use `python3.12 -m venv .venv` and `.venv/bin/python` instead of the Windows executable path.

## One-time website setup

You need an Azure subscription and permission to manage this GitHub repository. No Azure configuration can be completed by these files alone.

### 1. Create the Azure web app

On <https://portal.azure.com>:

1. Search for **App Services**, then select **Create → Web App**.
2. Choose your subscription and create or select a resource group.
3. Set a globally unique app **Name**, for example `yourname-assetdb`.
4. Set **Publish = Code**, **Runtime stack = Python 3.12**, and **Operating System = Linux**. Do not select Windows or a container deployment.
5. Choose a region and an App Service plan. **Basic B1** is a straightforward starter option with Always On; it incurs charges. Review pricing before creating resources.
6. Select **Review + create → Create**, then **Go to resource**.

If the creation wizard offers GitHub continuous deployment, leave it disabled: this repository already includes its workflow.

### 2. Configure startup and dependency installation

In the newly created App Service:

1. Open **Settings → Configuration → General settings** (the portal may place the startup command under **Stack settings**).
2. Set **Startup Command** to:

   ```text
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. Enable **Always On** if your plan supports it. Save/apply the changes.
4. Open **Settings → Environment variables → App settings**. In older portal layouts this is **Configuration → Application settings**.
5. Add **`SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`** and apply/save.

The workflow uploads tested source code and `requirements.txt`. This setting tells Azure's Oryx build system to install the Python dependencies on Linux. Do not upload your local `.venv`, and do not use `--reload` in the Azure startup command.

Also enable **HTTPS Only** under the app's configuration settings. Optionally configure **Monitoring → Health check** with the path `/health` if supported by your plan.

### 3. Obtain an Azure publish profile

This starter uses publish-profile authentication for a simple setup.

1. Under **Settings → Configuration → General settings**, enable **SCM Basic Auth Publishing Credentials**, then save. FTP basic authentication is not required and can remain disabled.
2. On the app's **Overview** page, select **Download publish profile** (sometimes called **Get publish profile**) in the toolbar.
3. Open the downloaded `.PublishSettings` file in a text editor. Its entire XML content will become a GitHub secret in the next step.

**Treat this file like a password. Never commit it, paste it into an issue, or include it in logs.** The repository ignores publish-profile files as an extra safeguard. Delete the local copy after storing it securely. If exposed, reset the app's publishing credentials and replace the GitHub secret.

If your organization prohibits SCM basic authentication, use an Azure OpenID Connect (OIDC) deployment instead; the included workflow would need to be changed to use `azure/login` and federated credentials. Do not bypass organizational policy.

### 4. Configure GitHub

On this repository's GitHub website:

1. Open **Settings → Secrets and variables → Actions**.
2. Under **Variables**, select **New repository variable**:

   | Name | Value |
   | --- | --- |
   | `AZURE_WEBAPP_NAME` | The exact Azure app name, such as `yourname-assetdb` — not its URL |

3. Under **Secrets**, select **New repository secret**:

   | Name | Value |
   | --- | --- |
   | `AZURE_WEBAPP_PUBLISH_PROFILE` | The entire XML content of the downloaded publish profile |

Use **repository** secrets/variables, not environment-scoped ones; this workflow does not declare a GitHub environment.

If Actions are disabled, enable them under **Settings → Actions → General**. Organization policies must allow `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, `actions/download-artifact`, and `azure/webapps-deploy`.

You do **not** need to create a second workflow in Azure **Deployment Center** or supply an Azure subscription ID for this publish-profile approach. Avoid having two workflows deploy the same app.

### 5. Push and deploy

Commit these files and push them to **`main`** using your editor's Git controls or Git. This setup assumes your deployment branch is named `main`; change both `refs/heads/main` conditions in the workflow if you use a different branch.

On GitHub, open **Actions → Test and deploy to Azure** and inspect the run:

1. **Build and test** installs dependencies and runs the tests.
2. After tests pass on `main`, **Deploy to Azure App Service** uploads the app.
3. Azure installs dependencies and starts the application. The first deployment can take several minutes.

If you configured Azure after your last push, use **Actions → Test and deploy to Azure → Run workflow**, select **main**, and run it. There is no need for an extra code change.

In Azure **Overview**, copy the app's **Default domain** and visit:

- `https://<default-domain>/`
- `https://<default-domain>/health`
- `https://<default-domain>/docs`

Use the actual domain shown in Azure; some apps have a generated suffix in the hostname.

## What happens on subsequent changes?

| GitHub event | Result |
| --- | --- |
| Push to any branch | Install dependencies and run tests |
| Pull request | Run tests; no production deployment |
| Push/merge to `main` | Run tests, then automatically deploy to Azure |
| Manual workflow run on `main` | Run tests, then deploy |
| Failed tests | Deployment does not run; the existing Azure app remains unchanged |
| `AZURE_WEBAPP_NAME` not configured | Tests still run; deployment is skipped |

Only `main` changes update the Azure app. Merge changes from other branches into `main` when ready. Deployment jobs are serialized to avoid simultaneous deployments. This starter deploys directly to the production app, so a restart/brief interruption is possible; deployment slots are an option for a future production setup.

## Troubleshooting

- **Deployment skipped:** check the `AZURE_WEBAPP_NAME` repository variable and ensure the workflow is running on `main`.
- **Missing publish profile / 401 / 403:** check the secret contains the entire profile for this app, and that SCM basic authentication is enabled. Replace the secret if publishing credentials were reset. App Service SCM access restrictions must also allow the GitHub runner to connect.
- **Deployment succeeds but app fails to start:** check Python 3.12, the startup command, and `SCM_DO_BUILD_DURING_DEPLOYMENT=true`. After changing that setting, deploy again. Review build logs in the Actions deployment step and Azure Deployment Center.
- **Startup errors / missing Python modules:** enable **App Service logs → Application logging (Filesystem)**, then open **Log stream**. Verify that Azure installed `requirements.txt` during deployment.
- **No deployment on push:** confirm these files are committed to GitHub, Actions are enabled, and your push/merge targets `main`.

## Files

- `app/main.py`: API routes and app configuration.
- `tests/test_main.py`: endpoint and documentation tests.
- `requirements.txt`: pinned runtime dependencies.
- `requirements-dev.txt`: local/CI testing dependencies.
- `.github/workflows/azure-webapp.yml`: automated tests and deployment.

The API is public and unauthenticated. Add authentication before introducing private asset data. This is a starter, not a database-backed asset-management system.

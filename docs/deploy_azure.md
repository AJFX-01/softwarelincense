# Deploying LicenseWise to Azure Container Apps

One container serves both the UI and the API, on port 8000. The image is stored in
GitHub Container Registry (GHCR), and Azure pulls it from there.

## What you need

- Azure CLI, installed with `brew install azure-cli`.
- Docker Desktop, running.
- A GitHub classic personal access token with the `write:packages` and `read:packages`
  scopes.
- The fine-tuned model in `models/deberta-v3-large-license-nli/`. That folder is
  gitignored, so the image must be built from a checkout that has it.

Put the secrets in your shell, not in files or commands that get saved:

```bash
export GHCR_USER=AJFX-01
read -s GHCR_TOKEN && export GHCR_TOKEN        # paste the GitHub token, then press Enter
set -a; source .env; set +a                    # loads GROQ_API_KEY
IMAGE=ghcr.io/ajfx-01/licensewise:latest       # GHCR names must be lowercase
```

## 1. Build and push the image

Run this from the project root. Container Apps runs on amd64 machines, so the build
targets amd64 even on an Apple-silicon Mac.

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
docker buildx build --platform linux/amd64 -t "$IMAGE" --push .
```

## 2. One-time Azure setup

```bash
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az group create -n licensewise-rg -l canadacentral
az containerapp env create -n licensewise-env -g licensewise-rg -l canadacentral
```

Azure for Students subscriptions allow only some regions. If `canadacentral` is refused
by a policy, use `eastus` or `westus2` instead.

## 3. Create the app

```bash
az containerapp create -n licensewise -g licensewise-rg --environment licensewise-env \
  --image "$IMAGE" \
  --registry-server ghcr.io --registry-username "$GHCR_USER" --registry-password "$GHCR_TOKEN" \
  --target-port 8000 --ingress external \
  --cpu 2 --memory 4Gi \
  --min-replicas 0 --max-replicas 1 \
  --secrets groq-key="$GROQ_API_KEY" --env-vars GROQ_API_KEY=secretref:groq-key \
  --query properties.configuration.ingress.fqdn -o tsv
```

The command prints the app's address. Open `https://<that address>`.

Why these settings:

- **`--cpu 2 --memory 4Gi`:** the verifier needs about 2 GB of memory, so 4 GiB leaves
  headroom. You can raise this to `--cpu 4 --memory 8Gi`, the most a Container Apps
  consumption plan allows, to make verification faster.
- **`--max-replicas 1`:** jobs and the job queue live in one process, so there must be
  only one copy of the app.
- **`--min-replicas 0`:** the app stops when nobody uses it, so it uses almost no credit.
  The first request after a pause waits about 1 to 2 minutes while Azure pulls the image
  and loads the model. For a demo, keep it running beforehand with
  `az containerapp update -n licensewise -g licensewise-rg --min-replicas 1`, and set it
  back to 0 afterwards. Running all the time costs roughly as much as the whole student
  credit in a month.
- **The GitHub token** is saved in Azure as a secret, only so Azure can pull the image.
  If the package is made public in GitHub (Packages, then licensewise, then Package
  settings), the three `--registry-*` options are not needed.

Run history is stored in SQLite inside the container, so it is wiped whenever the app
restarts or scales to zero.

## Update after a code change

```bash
docker buildx build --platform linux/amd64 -t "$IMAGE" --push .
az containerapp update -n licensewise -g licensewise-rg --image "$IMAGE" \
  --revision-suffix "v$(date +%m%d%H%M)"
```

The revision suffix makes Azure pull the image again even though the tag (`latest`) is the
same.

## Automatic deploys (push to main)

`.github/workflows/deploy.yml` runs on every push to `main` (a merged development PR). It
also runs when started by hand from the Actions tab. It builds the image on GitHub, pushes
it to GHCR, and updates the Container App. Pushes to `development` only run the CI checks.

Do these one-time steps after the app has been created by hand once (sections 1 to 3).

**A. Put the model where GitHub can download it.** `models/` is not in git, so the
workflow downloads the model from a GitHub Release. Pack it from the project root:

```bash
COPYFILE_DISABLE=1 tar --no-xattrs -cf deberta-v3-large-license-nli.tar -C models deberta-v3-large-license-nli
```

Then go to github.com/AJFX-01/softwarelincense, open **Releases** and choose **Draft a
new release**. Type the new tag `model-v1`, attach `deberta-v3-large-license-nli.tar`
(838 MB, under GitHub's 2 GB limit) and publish. If you retrain the model, upload it to
a new release and change `MODEL_RELEASE` in the workflow.

**B. Give GitHub an Azure login, limited to this resource group.**

```bash
SUB=$(az account show --query id -o tsv)
az ad sp create-for-rbac --name licensewise-deploy --role contributor \
  --scopes "/subscriptions/$SUB/resourceGroups/licensewise-rg" --json-auth
```

Copy the whole JSON it prints. In the GitHub repo, go to **Settings**, then **Secrets
and variables**, then **Actions**, and choose **New repository secret**. Name it
`AZURE_CREDENTIALS` and paste the JSON. Do not save the JSON anywhere else.

**C. Let the workflow push to the image package.** This applies only if you already
pushed the image from your Mac. On GitHub, open your profile, then **Packages**, then
**licensewise**, then **Package settings**. Under **Manage Actions access**, add the
`softwarelincense` repository with the **Write** role.

Each deploy tags the image with the commit, so Azure starts a new revision each time.
The first run takes about 10 to 15 minutes; later runs reuse cached layers and are much
faster. The app runs the same image as before, so its speed does not change.

## Check and debug

```bash
curl https://<address>/api/health
az containerapp logs show -n licensewise -g licensewise-rg --follow
```

## Remove everything (stops all charges)

```bash
az group delete -n licensewise-rg
```



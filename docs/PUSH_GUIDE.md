# Push and run from Junaed's account

Suggested repository: `junayedtiy4378/retail-sales-analytics`.

This is a new project. Keep NeuralPath and your GitHub profile repository separate.

## Publish from Windows

1. Extract the project ZIP to a new folder such as `D:\projects\retail-sales-analytics`.
2. Sign in to GitHub as junayedtiy4378. Create an empty repository called `retail-sales-analytics`. Leave README, .gitignore, and license initialization unchecked.
3. Open Command Prompt and run, adjusting the path to your extracted folder:

```bat
cd /d D:\projects\retail-sales-analytics
git init -b main
git config user.name "Junaed Ahmed"
git config user.email "junayedtiy437@gmail.com"
git remote add origin https://github.com/junayedtiy4378/retail-sales-analytics.git
git add .
git diff --cached --name-only
```

Review the staged list. It should include source, tests, SQL, the bundled synthetic data, README, and `.github/workflows/analytics.yml`. It should exclude `.venv`, `.cache`, and generated `reports`. Then:

```bat
git commit -m "Add retail sales analytics portfolio project"
git push -u origin main
```

Authenticate through GitHub's secure flow if prompted. If origin already exists, inspect `git remote -v` and use `git remote set-url origin https://github.com/junayedtiy4378/retail-sales-analytics.git` when this is the intended checkout. Do not force-push over an existing repository's work.

## Run without installing Python on your PC

Once pushed, open Actions → Test and build analytics reports. The first push should trigger it. You can also select Run workflow manually after the workflow exists on the default branch.

Open the successful run and download **retail-analysis-reports** from Artifacts. Extract it to access `dashboard.html`, `sales_analysis.xlsx`, charts, and the SQLite database. Opening the HTML report does not require a server. Artifact download may require signing in to GitHub.

No special tokens, API keys, environment variables, or PHP installation are required. This workflow belongs in this new project's repository, not inside the profile automation YAML.

## Add to your GitHub profile

After the new repository exists, add this to your profile README:

```markdown
### Retail Sales Analytics
Cleaned synthetic retail data using Python/Pandas, explored it with SQL, and generated an interactive dashboard and Excel reports, with automated tests in GitHub Actions.

[View the project](https://github.com/junayedtiy4378/retail-sales-analytics)
```

Add your own Power BI/Tableau screenshots and specific contributions as you extend the project. The supplied native BI dashboards are instructions to implement, not completed `.pbix`/Tableau files.

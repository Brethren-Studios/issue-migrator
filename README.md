# GitHub-to-BitBucket Issue Migrator

Migrate GitHub issue data to import-ready BitBucket issue data, following the formats specified by [GitHub's Issues API](https://developer.github.com/v3/issues/) and [BitBucket's issue data import documentation](https://confluence.atlassian.com/bitbucket/issue-import-export-data-format-330796872.html).

# Usage

Convert issues from this GitHub repository to BitBucket issue data, printed to stdout on the command line:

```bash
./migrateissuedata.py -o brethren-studios -r issue-migrator
```

Convert issues from this GitHub repository to BitBucket issue data, printed to stdout on the command line, with authenticated requests:

```bash
./migrateissuedata.py -o brethren-studios -r issue-migrator -u evanw555 -p "MYPASSWORD;)"
```

Convert issues from this GitHub repository to BitBucket issue data, saved to a file:

```bash
./migrateissuedata.py -o brethren-studios -r issue-migrator > bitbucket_friendly_issue_data.json
```

Get more help:

```bash
./migrateissuedata.py -h
```

# Details

This script works by making requests to the GitHub issue API for the specified repository, processing the fetched data, then outputting the resulting BitBucket issue data to the command line in JSON format.

Currently, [GitHub's API limits requests](https://developer.github.com/v3/rate_limit/) to `60` per hour for any IP address. Fortunately if you are authneticated, this limit is raised to `5000` requests per hour.

This script is currently only compatible with Python 3.

If you're having trouble running the script as is shown up above, try running in Python 3 explicitly with `python3 migrateissuedata.py [params...]`, or add executions privileges to your copy of the script with `sudo chmod +x migrateissuedata.py`

# Issues

If there are any issues with this script, please open a ticket. If there are any changes you'd like to contribute to this script, open a pull request. We here at Brethren Studios pride ourselves on responding to the needs of the open source community.

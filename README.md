# GitHub-to-BitBucket Issue Migrator

Migrate GitHub issue data to import-ready BitBucket issue data, following the formats specified by [GitHub's Issues API](https://developer.github.com/v3/issues/) and [BitBucket's issue data import documentation](https://confluence.atlassian.com/bitbucket/issue-import-export-data-format-330796872.html).

# Usage

```
usage: migrateissuedata.py [-h] -o ORG -r REPO [-u USERNAME] [-p PASSWORD]

Migrate GitHub issue data to import-ready BitBucket issue data.

optional arguments:
  -h, --help   show this help message and exit
  -o ORG       Name of the organization that owns the GitHub repo
  -r REPO      Name of the GitHub repo
  -u USERNAME  Username to authneticate requests
  -p PASSWORD  Password to authneticate requests
```

## Examples

Convert issues from this GitHub repository to BitBucket issue data, printed to stdout on the command line:

```bash
python3 migrateissuedata.py -o brethren-studios -r issue-migrator
```

Convert issues from this GitHub repository to BitBucket issue data, printed to stdout on the command line, with authenticated requests:

```bash
python3 migrateissuedata.py -o brethren-studios -r issue-migrator -u evanw555 -p "MYPASSWORD;)"
```

Convert issues from this GitHub repository to BitBucket issue data, saved to a file:

```bash
python3 migrateissuedata.py -o brethren-studios -r issue-migrator > bitbucket_friendly_issue_data.json
```

Get more help:

```bash
python3 migrateissuedata.py -h
```

# Details

This script works by making requests to the GitHub issues API for the specified repository, processing the fetched data, then outputting the resulting BitBucket issue data to the command line in JSON format.

## Compatibility

This script is currently only compatible with Python 3.

The examples shown up above explicitly run the script in Python 3 with `python3`, but your system might not have this alias. You can try running it with just `python` if your system default is Python 3. You can also run the script as an executable with `./migrateissuedata.py`, but you should make sure your copy of the file has the appropriate execution privileges with `sudo chmod +x migrateissuedata.py`

## Rate Limiting

Currently, [GitHub's API limits requests](https://developer.github.com/v3/rate_limit/) to `60` per hour for any IP address. Fortunately if you are authneticated, this limit is raised to `5000` requests per hour.

## Caching

It should be noted that this script makes use of caching in order to avoid hitting the rate limit. When a request is made to the GitHub issues API, the response data is cached in a hidden subdirectory of the working directory. This data persists between executions in order to provide caching between executions. If you'd like to clear the cache (necessary if the data you're migrating is updated) or if you'd just like to delete the files from your filesystem to free up space, then delete the subdirectory `.issuedata_cache/`

# Issues

If there are any issues with this script, please open a ticket. If there are any changes you'd like to contribute to this script, open a pull request. We here at Brethren Studios pride ourselves on responding to the needs of the open source community.

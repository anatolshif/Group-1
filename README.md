# Group-1
## Vulnerability Scanner
This project is a basic command-line tool for scanning for known vulnerabilities using the National Vulnerability Database (NVD) feeds. The scanner is designed to help automate the process of checking software and systems for security weaknesses.

## Core Functionality
The scanner's primary function is to:

Fetch and parse the latest NVD feeds, which contain detailed information on Common Vulnerabilities and Exposures (CVEs).

Provide a mechanism to cross-reference software or system information against this database to identify potential vulnerabilities.

Automate vulnerability checks, reducing the need for manual lookups and saving time in the security assessment process.

Best Practice
For the most accurate results, it is critical to keep the NVD feed data up-to-date. The tool is designed with a workflow that encourages a daily update of the vulnerability database.

## Prerequisites
To run this tool, you will need:

Python: This project is built entirely in Python.

NVD Feeds: Access to the official NVD feeds, which provide the raw data on CVEs.


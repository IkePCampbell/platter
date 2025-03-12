```
    ██████╗ ██╗      █████╗ ████████╗████████╗███████╗██████╗ 
    ██╔══██╗██║     ██╔══██╗╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
    ██████╔╝██║     ███████║   ██║      ██║   █████╗  ██████╔╝
    ██╔═══╝ ██║     ██╔══██║   ██║      ██║   ██╔══╝  ██╔══██╗
    ██║     ███████╗██║  ██║   ██║      ██║   ███████╗██║  ██║
    ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝
    
           ⚡ Jenkins CLI - Automate All The Things! ⚡
    
            [█████████████████████████████] 100%
                    Build Success! 🎉
```

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> A powerful CLI tool for Jenkins automation that makes your DevOps life easier! 🚀

Platter is a comprehensive command-line interface tool designed to streamline Jenkins operations and automate common tasks. It provides a simple and intuitive way to interact with your Jenkins instance, making CI/CD management a breeze.



## ✨ Features

- 📋 List and filter Jenkins jobs with detailed status information
- 🔄 Manage job configurations and SCM branches
- 🚀 Trigger builds with parameters and monitor progress
- 📊 View build logs and system information
- 🔌 List and manage plugins
- 🖥️ Monitor nodes and agents
- 📝 Handle build queues and job configurations

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- Jenkins instance with API access
- Jenkins API token

### Installation

1. Clone this repository:
```bash
git clone https://github.com/ikepcampbell/platter.git
cd platter
```

2. Install the required packages using pip:
```bash
# This will install compatible versions of all dependencies
pip3 install -r requirements.txt
```

3. Make the script executable and move it to your local bin:

Linux:
```bash
chmod +x platter.py
sudo cp platter.py /usr/local/bin/platter
```

MacOS:
```bash
chmod +x platter.py
sudo cp platter.py /usr/local/bin/platter
```

4. Configure your environment:

Add these variables to your ~/.bashrc (Linux) or ~/.zshrc (macOS):
```bash
export JENKINS_API_KEY="your-api-key"
export JENKINS_USERNAME="your-username"
export JENKINS_URL="http://localhost:8080"
alias platter="python3 /usr/local/bin/platter"
```

> 💡 To get your API key: Jenkins Dashboard → Your Profile → Configure → Add New API Token

5. Reload your shell configuration:
```bash
# For bash users
source ~/.bashrc

# For zsh users
source ~/.zshrc
```

## 🎯 Usage

Here are some common commands to get you started:

```bash
# List all jobs in root folder
platter list-jobs /

# Show job status
platter list-jobs /path --status

# Filter successful jobs
platter list-jobs /path --status --filter success

# Get SCM branch for a job
platter get-branch my-job

# Update SCM branch
platter replace-branch my-job feature/xyz

# Trigger a build and wait for completion
platter build my-job --wait

# View latest build logs
platter logs my-job

# Show system information
platter info

# List all nodes/agents
platter nodes

# View build queue
platter queue
```

For a complete list of commands:
```bash
platter --help
```

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🌟 Show your support

Give a ⭐️ if this project helped you!


## 📫 Contact

Isaac Campbell - [LinkedIn](https://www.linkedin.com/in/isaac-campbell/)

Co Created by Andy Wood - [LinkedIn](https://www.linkedin.com/in/andrew-wood-1899a630/)

Project Link: [https://github.com/ikepcampbell/platter](https://github.com/ikepcampbell/platter)

## 🙏 Acknowledgments

- [python-jenkins](https://python-jenkins.readthedocs.io/) for the excellent Jenkins API wrapper
- The Jenkins community for their amazing CI/CD platform
- All contributors who have helped shape this project

---

<p align="center">Made with ❤️ for the DevOps community</p>

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind, express or implied. The authors and maintainers of Platter take no responsibility for any production interruptions, system issues, or other problems that may arise from using this software. By using Platter, you acknowledge that you are using it at your own risk and that the authors cannot be held liable for any damages or issues resulting from its use.



Prereq's

1. Xmllint should come prepackaged with Python3, but double check that you have it.

2. Install python-jenkins with ```pip3 install python-jenkins```

3. Copy platter.py to /usr/local/bin

4. Go to Jenkins, click your profile, Configure, Add New Api Token. Call it whatever you like (I called mine localhost)

5. Take that API key, add these following variables in bash/zsh.

```
 export JENKINS_API_KEY="<API Key From Jenkins>"
 export USERNAME="<username>"
 export JENKINS_URL="<url>"
 alias platter="python3 /usr/local/bin/platter.py"
 ```

 source your bash/zsh before running the script

6. Run ```platter help``` to get started!

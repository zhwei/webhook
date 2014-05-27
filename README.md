# webhooks

## 使用说明

1. Create Json profile `configs/<project_name>.json`

  ```json

      {
        "name":"gotit",
        "location":"local",
        "branch": "2.0-stable",
      }
  ```
2. Create Bash Script file `shell/<project_name>.sh`

  ```bash
      #!/bin/bash
      cd "/path/to/project"
      git pull origin branch_name
      sudo /usr/local/bin/supervisorctl restart project_name
  ```

3. The stdout and stderr will be log to `logs/<project_name>.log`

## webhook url

    /hook/<project_name>/


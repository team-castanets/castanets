![Castanets Logo](https://user-images.githubusercontent.com/5627185/171138332-9cddf0f0-1fa0-477c-b3cb-61eaa1af4680.png)

--------------------------------------------------------------------------------

Castanets, Tool for Multi-stage Review Process

## How to Setup

### Writing Process Config (`castanets.yaml`)

```yaml
name: Process Name
description: Process Description
stages:
  - name: Stage 1
    label: stage_1
    description: |
      Stage 1 Description
    review:
      reviewers: ["username1", "username2"]
      must_review: ["username1"]
      minimum_approval: 1
    workflow:
      filename: stage_one.yaml
      inputs:
        jinja: {{ params.stage_one.param1 }}
        jinja-time: {% now 'Asia/Seoul', '%a, %d %b %Y %H:%M:%S' %}
        normal: param
        
```

- **name**: Process name
- **description**: Process description
- **stages**: List of stages
  - **name**: Stage name
  - **label**: Stage label (snake_case is recommended)
  - **description**: Stage description
  - **review**: Stage review settings
    - **reviewers**: Reviewers list (GitHub username)
    - **must_review**: Users who must review (GitHub username)
    - **minimum_approval**: Minimum approval required
  - **workflow**: GitHub Actions Workflow to run
    - **filename**: Github Actions Workflow filename (.github/workflows/<filename>, must subscribe on `workflow_dispatch`)
    - **inputs**: Workflow input

**IMPORTANT: Jinja template is enabled.** 

- **`params`**: Parameters written in GitHub Issue will be injected in `params` variable.
  - ex) `{{ params.param_a }}`
- **`github`**: Access to `GithubActionsContext`, defined in `models/contexts.py`.
  - ex) `{{ github.issue_id }}`
- **`state`**: Access to state saved in the Castanets' issue comment.
  - ex) `{{ state.workflow_output.output_a }}`
- **[Jinja2-Time](https://github.com/hackebrot/jinja2-time)**: you can get current time in config.**
  - ex) `{% now 'Asia/Seoul', '%a, %d %b %Y %H:%M:%S' %}`

### Github Actions Settings

- Add workflow under `.github/workflows`.
- The workflow must subscribe `issues (opened)`and `issue_comment (created)`.
- Also, prevent race condition with GitHub Actions' concurrency option.

```yaml
name: CL Process
on:
  issues:
    types: [opened]
  issue_comment: 
    types: [created]
concurrency: castanets-${{ github.ref }}
jobs:
  castanets-process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          token: ${{ secrets.PERSONAL_GITHUB_TOKEN }}
          submodules: true
      - name: Castanets
        id: castanets
        uses: ./.github/actions/castanets
        if: "contains(github.event.issue.title, '[CLPM]')"  # Issue title keyword filter
        with:
          config-path: castanets.yaml  # Process config path
          issue-autoclose: true  # Auto close issue after process
          token: ${{ secrets.PERSONAL_GITHUB_TOKEN }}  # Github PAT
          slack: true  # Enable Slack notification
          slack-token: ${{ secrets.SLACK_TOKEN }}  # Slack Webhook Token
          slack-channel: "#ml-pipeline-alert-test"  # Slack channel to send alert
```

## How to Use

### Start a process

Create an issue containing code block like ```yaml castanets. You have to add attribute `castanets` in code block.
Castanets will read the code block, and inject it to `params` variable in config's Jinja2 template.

Issue template is here: [.github/ISSUE_TEMPLATE/new_process.md](https://github.com/team-castanets/castanets/blob/main/.github/ISSUE_TEMPLATE/new_process.md)

### Stage review

Each Stage, Castanets makes the comment below. You can get detailed information about each stage, like reviewers and description of the stage.

---------------------------

## Click, clack. We are moving forward!

Review stage changed from **Start** to **Sampling**. [Workflow was triggered](https://google.com) for this stage.

```mermaid

    flowchart LR
        etl[ETL]:::Running --> labeling[Labeling]:::Pending --> training[Training]:::Pending

    classDef Done fill:#2da44e,stroke:#fff,color:white
    classDef Running fill:#bf8700,stroke:#fff,color:white
    classDef Pending fill:#888,stroke:#fff,color:white
    
```

### Stage Description

ETL Stage has been started! You can see the status of ETL process in [ETL Stage](https://google.com).

### Required Reviews
At least **1** approvals are needed to move this process forward.

Requested reviewers:

* @FYLSunghwan (MUST REVIEW)
* @harrydrippin 

<img src="https://user-images.githubusercontent.com/5627185/171138332-9cddf0f0-1fa0-477c-b3cb-61eaa1af4680.png" width="100px" align="right">

---------------------------

Each stage, you can use the command:

- `/approve`: Approve the current stage.
- `/dismiss`: Dismiss the current stage.
- `/rerun`: Rerun the current stage's workflow.
- `/clean_up`: Clean up current stage.
- `/stage_next`: Force move to next stage.
- `/finish`: Finish the process.

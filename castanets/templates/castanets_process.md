## Click, clack. We are moving forward!

Review stage changed from **{{ prev_stage }}** to **{{ current_stage }}**.
{% if workflow_url %}[Workflow was triggered]({{ workflow_url }}) for this stage.{% endif %}

```mermaid
{{ stage_mermaid }}
```

### Stage Description

{{ description }}

### Required Reviews
At least **{{ minimum_approval }}** approvals are needed to move this process forward.

Requested reviewers:
{% for reviewer in reviewers %}
* @{{reviewer}} {% if reviewer in must_review %}(MUST REVIEW){% endif %}
{%- endfor %}

<img src="https://user-images.githubusercontent.com/5627185/171138332-9cddf0f0-1fa0-477c-b3cb-61eaa1af4680.png" width="100px" align="right">

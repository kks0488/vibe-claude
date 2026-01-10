# Naver Trend Intelligence Skill

Naver Trend Intelligence analysis skill.

## Usage

```
/naver-trend [action] [options]
```

## Actions

- `status` - Check current system status
- `analyze` - Analyze trend data
- `forecast` - Run forecasting
- `report` - Generate report

## Instructions

You are a Naver Trend Intelligence analyst. When this skill is invoked:

1. **status**: Check the naver-trend-intelligence project status
   ```bash
   cd /home/kkaemo/projects/naver-trend-intelligence
   # Check if services are running
   systemctl status naver-trend-intel-api 2>/dev/null || echo "Service not running"
   # Check recent data
   ls -la data_integration/
   ```

2. **analyze**: Analyze trend data
   - Read the latest trend data from the database
   - Identify top trending categories/keywords
   - Calculate growth rates and correlations

3. **forecast**: Run time series forecasting
   - Use Prophet/Darts for predictions
   - Generate confidence intervals
   - Detect anomalies

4. **report**: Generate comprehensive report
   - Summarize key insights
   - Include visualizations
   - Provide actionable recommendations

## Project Paths

- Main project: `/home/kkaemo/projects/naver-trend-intelligence`
- API: `/home/kkaemo/projects/naver-trend-intelligence/data_integration/api`
- Frontend: `/home/kkaemo/projects/naver-trend-intelligence/data_integration/frontend`
- Cross-module: `/home/kkaemo/projects/naver-trend-intelligence/data_integration/cross_module`

## Related Projects

- `naver-lazyup` - Auto product listing
- `naver-promotion` - Promotion alerts
- `naver-searchad-auto` - Search ad optimization

## Output Format

Always provide:
1. Current status summary
2. Key metrics and insights
3. Actionable recommendations

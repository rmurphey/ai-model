# Performance Features

## Configuration Caching

Improves performance by caching scenario configurations and results:
- **40% faster** repeated runs with automatic result caching
- Cache statistics tracking (hits, misses, time saved)
- Configurable TTL (time-to-live) for cache entries
- Environment variable control: `AI_IMPACT_CACHE_ENABLED=false` to disable

```bash
# View cache performance
python main.py --scenario moderate_enterprise --cache-stats

# Disable caching for fresh calculations
python main.py --scenario moderate_enterprise --no-cache
```

## Sensitivity Analysis

Understand which parameters most influence your results:
- **Sobol indices** for global sensitivity analysis
- First-order effects (main effects) and total effects (including interactions)
- Partial dependence plots for parameter relationships
- Convergence metrics to ensure reliable results

```bash
# Run sensitivity analysis with default 512 samples
python run_analysis.py --sensitivity moderate_enterprise

# High-precision analysis with 2048 samples
python run_analysis.py --sensitivity moderate_enterprise --sensitivity-samples 2048
```

Output includes:
- Ranked parameter importance
- Variance explained by each parameter
- Interaction effects between parameters
- Tornado charts for visualization

## Batch Processing

Process multiple scenarios in parallel for comprehensive analysis:
- **Parallel execution** with configurable worker count
- Progress tracking with real-time updates
- Automatic comparison report generation
- Individual and aggregate result saving

```bash
# Use example batch configuration
python run_analysis.py --batch src/batch/batch_config.yaml

# Custom batch with specific worker count
python run_analysis.py --batch my_scenarios.yaml --batch-workers 8
```

Batch configuration example:
```yaml
scenarios:
  - conservative_startup
  - moderate_enterprise
  - aggressive_scaleup
parallel_workers: 4
output_dir: outputs/batch
generate_comparison: true
save_individual_reports: true
```
# Economist Agent - Claude Code Agents

This directory contains specialized agents for the Economist Agent system, a multi-agent economic research assistant built with Streamlit and Autogen AgentChat.

## Agent Architecture Overview

The Economist Agent system uses a multi-agent architecture with the following core components:
- **Data Analyst Agent**: Proposes specifications, checks identification assumptions, explains methods
- **Code Executor Agent**: Runs Python analysis in a sandbox and returns safe artifacts
- **Retriever Agent**: Provides literature and documentation lookups via local RAG

These Claude Code agents extend the system with specialized capabilities for economic research.

## Available Agents

### Core Development Agents

#### `core/researcher.md`
- **Purpose**: Deep research and information gathering specialist for economic analysis
- **Capabilities**: Economic data analysis, pattern recognition, literature research, econometric methodology evaluation
- **Use When**: Need comprehensive research on economic topics, data exploration, or literature review

#### `core/planner.md` 
- **Purpose**: Strategic planning and task orchestration for economic analysis workflows
- **Capabilities**: Economic task decomposition, methodology planning, resource allocation, risk assessment
- **Use When**: Complex economic research tasks that need structured planning and coordination

#### `core/coder.md`
- **Purpose**: Implementation specialist for Python economic analysis code
- **Capabilities**: Econometric implementation, data processing pipelines, statistical analysis, economic visualizations
- **Use When**: Need to implement econometric models, data analysis workflows, or statistical computations

### Documentation & Quality Assurance

#### `documentation-manager.md`
- **Purpose**: Expert documentation specialist for economic research projects
- **Capabilities**: Methodology documentation, results documentation, data documentation, economic interpretation
- **Use When**: After analysis completion to ensure proper documentation of economic methods and findings

#### `validation-gates.md` (Existing)
- **Purpose**: Testing and validation specialist for economic analysis code
- **Capabilities**: Statistical validation, code testing, robustness checks, quality gates
- **Use When**: After implementing economic analysis to validate correctness and reliability

### Specialized Economic Analysis

#### `data/ml/econometric-ml-model.md`
- **Purpose**: Machine learning applications in economics and econometric modeling
- **Capabilities**: Economic forecasting, causal inference ML, time series ML, panel data ML
- **Use When**: Need to apply ML techniques to economic problems while maintaining economic validity

#### `analysis/economic-code-analyzer.md`
- **Purpose**: Code quality analysis specialized for economic analysis code
- **Capabilities**: Econometric implementation validation, economic logic verification, statistical assumption checking
- **Use When**: Review economic analysis code for quality, correctness, and best practices

## Agent Integration Workflow

### Typical Economic Analysis Workflow
1. **Planning Phase**: `planner.md` creates analysis strategy and task breakdown
2. **Research Phase**: `researcher.md` investigates data, literature, and methodology
3. **Implementation Phase**: `coder.md` implements econometric analysis and visualizations
4. **ML Enhancement**: `econometric-ml-model.md` adds forecasting or causal inference capabilities
5. **Quality Assurance**: `validation-gates.md` and `economic-code-analyzer.md` validate results
6. **Documentation**: `documentation-manager.md` creates comprehensive documentation

### Agent Coordination
- Agents share context through the Autogen framework
- Each agent has specific triggers and capabilities
- Agents can delegate tasks to other specialized agents
- Quality gates ensure economic validity at each stage

## Economic Research Capabilities

### Econometric Analysis
- Time series analysis with proper temporal handling
- Panel data methods with entity/time fixed effects
- Causal inference with IV, RDD, and experimental methods
- Diagnostic testing and robustness checks

### Machine Learning Applications
- Economic forecasting with feature engineering
- Causal machine learning (Double ML, Causal Forests)
- Time series forecasting with economic constraints
- Panel data ML with proper cross-validation

### Data Processing
- Economic variable transformations (logs, growth rates, lags)
- Missing data handling appropriate for economic time series
- Outlier detection and treatment for economic data
- Data validation against economic logic

### Visualization & Reporting
- Publication-quality economic charts and graphs
- Regression diagnostic plots
- Time series decomposition visualizations
- Economic interpretation of statistical results

## Usage Guidelines

### When to Use Each Agent
- **Complex multi-step analysis**: Start with `planner.md`
- **Need economic context/theory**: Use `researcher.md`
- **Implement econometric models**: Deploy `coder.md`
- **Add ML capabilities**: Engage `econometric-ml-model.md`
- **Ensure code quality**: Run `economic-code-analyzer.md`
- **Final documentation**: Execute `documentation-manager.md`

### Best Practices
1. **Economic Theory First**: Always ground analysis in established economic theory
2. **Proper Identification**: Consider causal identification challenges in observational data
3. **Robustness**: Test sensitivity to different specifications and samples
4. **Economic Significance**: Consider practical importance alongside statistical significance
5. **Reproducibility**: Ensure all analysis steps can be replicated

### Integration with Existing System
These agents work alongside the existing Economist Agent architecture:
- Data uploaded via Streamlit sidebar is available to all agents
- Code execution happens in the isolated `code_executor/` workspace
- Generated visualizations are automatically displayed in chat
- All LLM calls remain local via Ollama for data security

## File Structure
```
.claude/agents/
├── README.md (this file)
├── validation-gates.md (existing)
├── documentation-manager.md
├── core/
│   ├── researcher.md
│   ├── planner.md
│   └── coder.md
├── data/
│   └── ml/
│       └── econometric-ml-model.md
└── analysis/
    └── economic-code-analyzer.md
```

## Dependencies

These agents expect the following Python libraries to be available:
- **Core**: pandas, numpy, matplotlib, seaborn
- **Econometrics**: statsmodels, scipy
- **Machine Learning**: scikit-learn, xgboost (optional)
- **Time Series**: pandas time series functionality
- **Causal Inference**: (optional specialized libraries)

All dependencies should be installed in the environment running the Economist Agent system.

## Contributing

When adding new agents:
1. Follow the established naming convention: `category-specialization.md`
2. Include proper metadata headers with triggers and capabilities
3. Provide economic context and theory guidance
4. Ensure integration with existing agent workflow
5. Add appropriate economic validation and quality checks
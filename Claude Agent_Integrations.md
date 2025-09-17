### **1. Core Development Framework**
- **`core/researcher.md`** - Perfect fit for your Retriever Agent functionality
- **`core/planner.md`** - Strategic planning for complex economic analysis tasks
- **`core/coder.md`** - Implementation specialist for Python analysis code
- **`documentation-manager.md`** - Keep documentation synchronized with code changes

### **2. Data & ML Specialized**
- **`data/ml/data-ml-model.md`** - Essential for economic modeling and ML analysis
- **`analysis/code-analyzer.md`** - Code quality for Python analysis scripts

### **3. Quality & Validation**
- **`validation-gates.md`** - Already present, keeps your analysis reliable

## **Recommended Implementation**

### **Essential Agents Copied & Adapted**

1. **Core Framework** (3 agents)
   - `core/researcher.md` - Economic research specialist with literature review and data analysis capabilities
   - `core/planner.md` - Strategic planning for complex economic analysis workflows  
   - `core/coder.md` - Python implementation specialist for econometric analysis

2. **Documentation & Quality** (2 agents)
   - `documentation-manager.md` - Economic research documentation specialist
   - `validation-gates.md` - Already existed, validates analysis quality

3. **Specialized Economic Analysis** (2 agents)
   - `data/ml/econometric-ml-model.md` - ML applications in economics (forecasting, causal inference)
   - `analysis/economic-code-analyzer.md` - Code quality analysis for econometric implementations

### **Key Adaptations for Economist Agent**

- **Economic Context**: All agents adapted with economic theory, econometric methods, and research best practices
- **Time Series Focus**: Proper handling of temporal data, no lookahead bias, appropriate validation
- **Causal Inference**: Built-in considerations for identification strategies and causal validity
- **Integration**: Designed to work with your existing Streamlit + Autogen + Ollama architecture

### **Workflow Integration**

The agents create a complete economic analysis pipeline:
1. **Planner** → Breaks down complex economic research questions
2. **Researcher** → Provides economic context and methodology guidance  
3. **Coder** → Implements econometric analysis in Python
4. **ML Developer** → Adds forecasting/causal inference capabilities
5. **Code Analyzer** → Validates economic logic and statistical correctness
6. **Documentation Manager** → Creates comprehensive research documentation

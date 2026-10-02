# Target hybrid retrieval pipeline

This diagram shows the planned statutory retriever. The original query remains available while a bounded rewrite adds search terms. Both paths use BM25 and dense embeddings, with ranked results fused before and after graph expansion. This exact combination has not yet been evaluated as a deployed system.

```mermaid
flowchart LR
    Q["Lawyer question"] --> O["Original query"]
    Q --> RW["Bounded query rewrite"]
    RW --> S["Sanitized rewrite"]

    O --> OB["BM25 lexical"]
    O --> OD["Dense embeddings"]
    S --> RB["BM25 lexical"]
    S --> RD["Dense embeddings"]

    OB --> F1["RRF fusion"]
    OD --> F1
    RB --> F1
    RD --> F1

    F1 --> G["Typed graph expansion"]
    F1 --> F2["Final RRF"]
    G --> F2
    F2 --> C["Cited sections"]
    C --> AG{"Answer gate"}
    AG --> A["Grounded answer"]
    AG --> X["Insufficient authority"]

    classDef input fill:#002FA7,color:#FFFFFF,stroke:#002FA7,stroke-width:1px
    classDef query fill:#E8EEFC,color:#002FA7,stroke:#002FA7,stroke-width:1px
    classDef search fill:#FFFFFF,color:#0A0A0A,stroke:#8A98B8,stroke-width:1px
    classDef process fill:#E8EEFC,color:#002FA7,stroke:#002FA7,stroke-width:1px
    classDef output fill:#002FA7,color:#FFFFFF,stroke:#002FA7,stroke-width:1px

    class Q input
    class O,RW,S query
    class OB,OD,RB,RD search
    class F1,G,F2,C,AG process
    class A,X output
```

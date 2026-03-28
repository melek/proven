# Formal Verification and Runtime Monitoring of Operational Procedures in Safety-Critical Systems: A Systematic Literature Review

## Abstract

This review addresses the question: *What approaches exist for formal verification and runtime monitoring of operational procedures in safety-critical systems?* Through a systematic search of Semantic Scholar and arXiv (2010--2026), followed by one round of backward and forward snowballing, 388 candidate papers were identified. After screening against five inclusion and four exclusion criteria, 98 papers were included in the final corpus. The evidence is organized into six themes: (1) model checking of procedural logic, (2) runtime verification and temporal monitoring, (3) assurance cases and structured safety arguments, (4) domain-specific PLC and industrial verification, (5) scenario-based and simulation-driven validation, and (6) specification engineering and the bridge from natural language to formal methods. Key findings indicate that model checking and runtime verification are the dominant verification strategies, but most work operates at whole-procedure granularity rather than at the step or assertion level. The assurance case community has developed a mature ecosystem of tools and metamodels (SACM, GSN) with increasing integration of formal proofs, yet the gap between design-time assurance and runtime monitoring remains partially bridged. The specification bottleneck -- the difficulty of writing formal specifications -- persists as a major adoption barrier, though recent LLM-assisted and automated synthesis approaches show promise. These findings have direct implications for systems that declare procedures with preconditions, postconditions, and effect declarations, suggesting that hybrid approaches combining static proof with runtime monitoring offer the most practical path to verified procedural execution.

## 1. Introduction

Safety-critical systems in aviation, nuclear energy, healthcare, automotive, railway, and maritime domains rely on operational procedures -- structured sequences of steps with defined preconditions, postconditions, and expected effects -- to ensure safe operation. When these procedures are executed by automated systems (PLCs, flight controllers, autonomous agents) or followed by human operators, the question of whether they are correct, complete, and safe becomes paramount.

Formal verification offers mathematical guarantees that a system satisfies its specification. Runtime monitoring provides continuous assurance during execution. Between these poles lie hybrid approaches, scenario-based testing, simulation-driven validation, and structured safety argumentation. This review systematically maps the landscape of approaches for verifying and monitoring operational procedures in safety-critical contexts.

The review addresses three sub-questions:

1. What verification strategies are used for declared operational procedures -- static proof, runtime monitoring, hybrid, or testing-based?
2. How are procedures decomposed for verification -- at what granularity (step-level, precondition/postcondition pairs, effect declarations, whole-procedure invariants)?
3. What criteria determine when a procedure is considered sufficiently verified -- and what levels of assurance exist on the spectrum from "monitored" to "proven"?

The remainder of this review is structured as follows. Section 2 describes the systematic review methodology. Section 3 presents findings organized by six themes. Section 4 discusses cross-cutting observations, gaps, and implications. Section 5 concludes with answers to the sub-questions and future directions.

## 2. Methodology

### 2.1 Search Strategy

The search was conducted across two databases:

- **Semantic Scholar** (3 queries): targeting "formal verification" + "operational procedures" + "safety-critical"; "runtime monitoring" + "standard operating procedures" + verification; and DO-178C/IEC 61508/FDA/ECSS + "procedure verification"
- **arXiv** (2 queries): targeting "runtime verification" + "procedures" + "safety" (cs.SE, cs.FL, cs.AI); and "formal methods" + "operational procedures" (cs.SE, cs.FL)

Five queries were executed, retrieving up to 50 results each. The date range was 2010--2026. Language was restricted to English.

### 2.2 Selection Criteria

**Inclusion criteria:**

| ID | Description |
|----|-------------|
| IC1 | Addresses verification, validation, or runtime monitoring of operational procedures |
| IC2 | Procedures are structured/declared (not ad-hoc scripts or free-form workflows) |
| IC3 | Safety-critical or high-assurance context |
| IC4 | Published 2010--2026 |
| IC5 | English language |

**Exclusion criteria:**

| ID | Description |
|----|-------------|
| EC1 | Pure software verification with no procedural/operational component |
| EC2 | Survey without original contribution |
| EC3 | Not retrievable |
| EC4 | Less than 4 pages |

### 2.3 Screening Process

A total of 102 candidates were identified from database searches. After abstract-level screening against all inclusion and exclusion criteria, 22 papers were included from the search phase. Two papers were flagged for full-text review. The overall screening encompassed 390 decisions (including snowball candidates), yielding 98 included papers and 290 exclusions.

### 2.4 Snowballing

One round of backward and forward snowballing was conducted on the initial included set. 286 additional candidates were discovered (193 from backward citation tracing, 93 from forward citations). After screening, 76 papers were added, bringing the final included corpus to 98 papers.

### 2.5 Data Extraction

For each included paper, the following fields were extracted: domain, procedure formalism, verification approach (static proof, runtime monitoring, testing, model checking, hybrid, other), verification granularity (whole-procedure, phase-level, step-level, assertion-level, effect-level), assurance level (proven, validated, monitored, tested), tool support, and key finding. Extraction was performed from abstracts (for papers without full-text access) and from full text where available.

### 2.6 Threats to Validity

Several limitations affect this review:

- **Inference-based screening**: Screening decisions were made by an AI system on the basis of abstracts and metadata. Some relevant papers may have been incorrectly excluded, and some marginally relevant papers may have been included.
- **Corpus changes over time**: The databases were queried at a single point in time (March 2026). Subsequent publications are not captured.
- **Query coverage**: The search terms, while designed to be comprehensive, may not capture all relevant terminology (e.g., "workflow verification," "process mining for safety," or domain-specific terms in non-English-origin literature).
- **Extraction from abstracts**: For papers where only the abstract was available, extraction fields may have lower confidence. 46 papers were extracted from abstracts only.
- **No formal risk-of-bias assessment**: Individual study quality was assessed via a checklist (QA1--QA5) but no formal risk-of-bias tool (e.g., ROBINS-I) was applied.
- **No effect-size synthesis**: This is a qualitative thematic synthesis. No meta-analysis of quantitative outcomes was performed.
- **No certainty-of-evidence assessment**: No GRADE or equivalent framework was applied to rate the overall certainty of the synthesized evidence.

## 3. Findings

### 3.1 Overview

| Metric | Count |
|--------|-------|
| Candidates identified from database search | 102 (from 5 queries across 2 databases) |
| Candidates identified from snowballing | 286 |
| Total candidates | 388 |
| Total screened | 390 |
| Excluded | 290 |
| Flagged for full-text | 2 |
| Final included | 98 |

The 98 included papers span 2011--2026, with the largest concentrations in 2025 (19 papers), 2024 (11 papers), and 2018 (10 papers). By verification approach, model checking dominates (26 papers), followed by hybrid methods (23), survey/other (16), static proof (14), runtime monitoring (10), and testing (9). The majority of papers operate at whole-procedure granularity (59), with assertion-level verification as the second most common (24). Proven assurance is claimed by 33 papers, validated by 46, monitored by 15, and tested by 3.

The domains represented include general/cross-domain (33), embedded systems (22), aviation (12), automotive (10), nuclear (6), maritime/other (5 each), railway (3), space (3), healthcare (2), and business processes (2).

### 3.2 Findings by Theme

#### 3.2.1 Model Checking of Procedural and System Logic

Model checking -- the exhaustive exploration of a system's state space against temporal logic specifications -- is the most frequently applied verification strategy in this corpus, appearing in 26 papers.

**Temporal logic specifications.** The majority of model checking work formalizes safety requirements as Linear Temporal Logic (LTL) or Computation Tree Logic (CTL) properties. Schmid et al. verified fail-operational arbitration logic for automated driving using NuSMV with LTL specifications encoding ISO 26262 safety goals [@schmid2021]. Miao et al. applied SPIN model checking with LTL to verify fault protection functions in civil aircraft high-lift control systems, translating Simulink/Stateflow models to Promela [@miao2025]. Bahig et al. demonstrated formal verification of automotive designs against ISO 26262 requirements using model checking [@bahig2017]. Mak et al. performed the first symbolic and safety-centric formal verification of the MAVLink protocol for autonomous eVTOL vehicles, targeting communication integrity in safety-critical UAM contexts [@mak2025].

**Timed and parameterized models.** Where timing constraints are critical, timed automata and tools such as UPPAAL provide the modeling framework. Recta et al. modeled ETCS Moving Block railway route management as UPPAAL timed automata, enabling safety analysis through simulation and parametric queries [@recta2025]. Hasrat et al. combined UPPAAL statistical model checking with reinforcement learning to optimize safe failure fractions in industrial drive systems [@hasrat2025a; @hasrat2025b]. Chen et al. proposed a hierarchical approach combining STPA hazard analysis with Event-B formal modeling and refinement for railway ATP systems, demonstrating how layered abstractions manage verification complexity [@chen2025].

**Scalability.** A persistent challenge is state-space explosion. Pike demonstrated k-induction as a technique for real-time system verification that avoids full state enumeration [@pike2013]. Sachtleben et al. proved that mathematical safety proofs in Isabelle/HOL for distributed railway interlocking systems are network-independent and thus scale where model checking grows exponentially [@sachtleben2024]. Fritzsch et al. reported industrial experience applying NuSMV at scale to vehicle control systems, documenting practical strategies for managing complexity [@fritzsch2020]. Hu et al. compared Simulink and SCADE for real-time system modeling and automatic code generation, finding that tool choice significantly affects verification feasibility for embedded flight control systems [@hu2026].

**Areas of consensus.** Model checking is widely accepted as effective for finite-state procedural logic with well-defined safety properties. The approach provides exhaustive coverage within the modeled state space, and tools like NuSMV, SPIN, and UPPAAL have mature ecosystems.

**Debates.** The fundamental tension between model checking's exhaustiveness and its scalability limitations remains unresolved. Papers diverge on whether abstraction-based model checking or theorem-proving-based approaches are preferable for industrial-scale systems.

**Gaps.** Few papers address model checking of procedures that involve continuous dynamics, human decision points, or learning-enabled components. The connection between a verified model and the actual deployed system (the "model fidelity" problem) receives limited attention.

#### 3.2.2 Runtime Verification and Temporal Monitoring

Runtime verification -- monitoring system execution traces against formal specifications -- represents the primary lightweight alternative to exhaustive static analysis. This theme encompasses 10 papers directly on runtime monitoring plus several hybrid approaches.

**Foundational frameworks.** Havelund and Peled traced the progression from propositional to first-order temporal logic for runtime verification, establishing the theoretical foundations for monitoring data-rich traces [@havelund2018]. Kuester advanced this by defining LTLFO (first-order LTL) for data-carrying traces and introducing spawning automata as an efficient monitoring mechanism [@kuester2016]. Rozier identified the specification bottleneck as the biggest impediment to runtime verification adoption in autonomous systems [@rozier2016].

**Metric temporal logic.** Several papers address monitoring with real-time constraints. Raha et al. developed TEAL, an SMT-based algorithm for synthesizing efficiently monitorable MTL formulas with bounded future-reach [@raha2023]. Lima et al. produced explainable MTL monitors with proof-tree verdicts, formally verified in Isabelle/HOL [@lima2023]. Chattopadhyay and Mamouras contributed a verified online monitor for MTL with quantitative semantics [@chattopadhyay2020].

**Domain applications.** McColl et al. extended runtime verification to energy properties within FPGA-based hardware/software co-design for space missions [@mccoll2025]. Watanabe et al. demonstrated Signal Temporal Logic (STL) based runtime monitoring for detecting unsafe feature interactions between ADAS systems in an industrial automotive case study [@watanabe2018]. Mao et al. applied Past Linear Temporal Logic (PPLTL) for runtime verification of security and safety properties in PLC-based industrial control systems [@mao2022]. In the nuclear domain, Lapuh et al. implemented a continuous 3D displacement monitoring system for power plant piping that has operated for over three years under radiation conditions, verifying that operational procedures do not induce excessive dynamic displacements [@lapuh2026]. Molent et al. validated an individual aircraft fatigue monitoring system using quantitative fractography, demonstrating runtime structural health monitoring as a form of procedural compliance verification [@molent2012].

**Stream-based monitoring.** Gorostiaga et al. introduced HLola, an extensible stream runtime verification engine via Haskell DSL embedding, validated in online UAV monitoring scenarios [@gorostiaga2021].

**Areas of consensus.** Runtime verification is recognized as complementary to, not a replacement for, static verification. It is particularly valued where complete formal verification is infeasible (e.g., learning-enabled components, open environments).

**Gaps.** The connection between specification synthesis and runtime monitoring remains underdeveloped. Most runtime verification papers assume specifications are given, while the specification engineering literature (Theme 3.2.6) treats specification creation separately.

#### 3.2.3 Assurance Cases and Structured Safety Arguments

Structured safety argumentation through assurance cases constitutes the largest single conceptual cluster in this corpus, with 13 papers tagged for assurance cases and related concepts (SACM, GSN, model-based assurance, assurance case tooling).

**The SACM ecosystem.** Wei et al. developed the ACCESS methodology for assurance-case-centric engineering of safety-critical systems, integrating Isabelle/HOL-verified RoboChart models with SACM-based argument structures [@wei2024a]. The SACM metamodel, standardized by OMG, provides a richer foundation than GSN or CAE alone; Wei et al. demonstrated its expressiveness through transformations and tooling [@wei2019]. Nemouchi et al. introduced Isabelle/SACM, enabling computer-assisted assurance case construction with integrated formal proofs [@nemouchi2019]. Wei et al. also developed DECISIVE, an iterative automated safety analysis approach that drives safety-critical system design through automated hazard identification and mitigation [@wei2022; @wei2024b], and proposed constrained natural language (CNL) for automated validation of assurance case argument rules [@wei2024c].

**Formal evidence generation.** A significant research direction connects formal proofs directly to assurance case evidence. Foster et al. demonstrated Isabelle/SACM for autonomous underwater vehicle assurance, encoding SI metric units and RoboChart behavioral models with formal proofs [@foster2020]. Yan et al. extended this to systematic formal evidence generation from RoboChart models using model checking and theorem proving [@yan2026]. Prokhorova et al. showed how Event-B refinement proofs can be systematically mapped to safety case argument structures [@prokhorova2015]. Gleirscher et al. traced the evolution of formal model-based assurance cases for autonomous robots, introducing reusable argument patterns with formally verified evidence [@gleirscher2019]. Hawkins et al. proposed a model-based weaving approach that systematically links assurance case arguments to design artifacts [@hawkins2015].

**Tool support.** The community has produced several tools: CertWare, an Eclipse-based workbench supporting GSN and CAE [@barry2011]; AdvoCATE from NASA for systematic assurance case development [@denney2017]; Resolute, a domain-specific language for generating assurance cases from AADL architecture models [@gacek2014]; the ACME environment for ACCESS [@wei2024a]; Utsunomiya et al. developed a tool to create assurance cases through models, linking system models to argument structures [@utsunomiya2018]; and Netkachova et al. proposed building blocks for modular assurance case construction using the CAE notation [@netkachova2015]. Lin et al. contributed a framework specifically targeting the generation and ongoing maintenance of assurance cases as systems evolve [@lin2016].

**Dynamic and runtime assurance.** Denney and Pai introduced dynamic safety cases for through-life safety assurance, enabling proactive monitoring during operation [@denney2015]. Calinescu et al. developed ENTRUST, combining design-time and runtime verification with industry assurance processes [@calinescu2017]. Wei et al. addressed the design-time to runtime transition for model-based assurance cases [@wei2018]. Myklebust et al. explored the integration of agile safety cases with DevOps practices in the automotive industry, enabling continuous safety argumentation alongside iterative development [@myklebust2020].

**AI-specific assurance.** Recent work extends assurance cases to AI/ML systems. Lee et al. introduced taxonomies for AI-specific safety case claim types [@lee2026]. Davidson et al. applied the AMLAS process using GSN to autonomous vehicle ML components [@davidson2025]. Ayora et al. described the REBECCA framework for Edge-AI assurance [@ayora2024].

**Areas of consensus.** Assurance cases provide a structured, auditable framework for safety argumentation. The integration of formal methods with assurance case metamodels (particularly SACM) is a clear trend. Tool support has matured significantly since 2011.

**Contradictions.** Some authors argue that assurance cases are sufficient for certification (providing a complete safety argument), while others contend they document rather than create safety -- the argument is only as strong as its evidence. Habli et al. found that health IT safety assurance in England lacks formal underpinning despite systematic risk management processes [@habli2018].

**Gaps.** Automated maintenance of assurance cases as systems evolve remains challenging. Few papers address assurance cases for procedures that change frequently (e.g., configurable safety systems). The connection between assurance case verdict and operational permission (can/should the system continue operating if part of its safety case is invalidated?) is underexplored.

#### 3.2.4 PLC and Industrial Control Verification

Programmable Logic Controller (PLC) verification forms a distinctive cluster of 8 papers, primarily centered on the PLCverif tool ecosystem developed at CERN.

**The PLCverif platform.** Lopez-Miguel et al. established formal verification of PLCs as a service, demonstrating compliance with IEC 61508/61511 at the CERN-GSI particle accelerator facility, including methods for handling know-how-protected (proprietary) library functions through simulation and timing diagram reverse-engineering [@lopezmiguel2025]. The PLCverif tool was progressively reported: Lopez-Miguel et al. described its status and capabilities for verifying PLC programs using multiple backend model checkers [@lopezmiguel2022]. Adiego et al. applied it to the highly-configurable SPS Personnel Protection System at CERN, demonstrating that model checking can handle safety-critical software that undergoes frequent configuration changes [@adiego2022]. An earlier ITER fusion reactor case study further validated the approach for nuclear-class safety systems [@adiego2018].

**Scaling to industrial programs.** Adiego et al. demonstrated model checking on industrial-sized PLC programs, addressing the scalability challenges that had previously limited formal verification to small examples [@adiego2015]. Xiong et al. proposed a user-friendly verification approach for IEC 61131-3 PLC programs aimed at practitioners without deep formal methods expertise [@xiong2020]. Lee et al. developed bounded model checking for PLC Structured Text programs using rewriting modulo SMT [@lee2022].

**Nuclear and particle physics applications.** Pakonen reported practical applications of model checking in the Finnish nuclear industry [@pakonen2017]. Das et al. used Petri nets to model and verify nuclear power plant shutdown procedures [@das2024].

**Areas of consensus.** PLC verification via model checking is technically mature, with proven industrial applicability at CERN, ITER, and in the Finnish nuclear industry. The verification-as-a-service model, where formal methods expertise is provided externally rather than requiring it of every development team, is an emerging organizational pattern [@lopezmiguel2025; @tao2025].

**Gaps.** Integration of PLC verification into standard development workflows (CI/CD-style continuous verification) is not yet established. Verification of PLC programs that interact with learning-enabled components or adaptive control algorithms is unaddressed.

#### 3.2.5 Scenario-Based and Simulation-Driven Verification

Scenario-based verification uses defined operational scenarios to test and validate system behavior. This theme spans 6 papers on scenario-based approaches plus simulation-related work.

**Scenario specification languages.** Fremont et al. introduced Scenic, a probabilistic programming language for specifying scenarios as distributions over scenes, enabling systematic generation of test cases for autonomous systems [@fremont2018]. Barbosa et al. used MTL safety specifications in the D4+ framework for scenario-based adversarial testing of autonomous vehicles [@barbosa2025]. Riedmaier et al. provided a comprehensive taxonomy for scenario-based safety assessment of automated vehicles, proposing combinations of formal verification with simulation [@riedmaier2020].

**Contract-based and lifecycle approaches.** Hake et al. integrated scenario-based and contract-based verification for automated vessels, using verification descriptors to translate safety requirements into testable contracts that span the entire lifecycle [@hake2024]. Holthusen et al. proposed multi-viewpoint contracts for negotiating embedded software updates, splitting verification between laboratory and field environments [@holthusen2016]. Heikkila et al. described a goal-based safety qualification process for an autonomous ship prototype, applying structured safety arguments to maritime operational procedures [@heikkil2017]. Kocahan et al. conducted functional safety analysis of a fail-operational steer-by-wire system following ISO 26262, demonstrating scenario-driven hazard analysis for automotive drive-by-wire procedures [@kocahan2024].

**Simulation validation.** Bestmann et al. reported lessons from setting up DO-384-compliant Monte Carlo simulation for validating aircraft integrity monitoring algorithms [@bestmann2023]. Reiher et al. reviewed the state of scenario-based and simulation-based V&V for autonomous maritime systems [@reiher2021].

**Falsification-based approaches.** Dreossi et al. developed VerifAI, a toolkit combining temporal-logic falsification with fuzz testing and parameter synthesis for simulation-based verification of AI systems [@dreossi2019].

**Areas of consensus.** Scenario-based verification is considered essential for systems operating in open, partially observable environments where exhaustive formal verification is infeasible. The automotive and maritime communities have converged on scenario-based approaches as a primary means of safety assessment.

**Gaps.** Completeness of scenario coverage remains an open problem -- how many scenarios are "enough"? The relationship between scenario-based testing results and formal assurance levels is not well-defined.

#### 3.2.6 Specification Engineering: From Natural Language to Formal Methods

The specification bottleneck -- identified by Rozier as the biggest barrier in formal methods and autonomy [@rozier2016] -- is addressed by a growing body of work on automated specification creation and natural-language-to-formal-method translation.

**LLM-assisted specification.** Endres et al. showed that LLMs can translate informal natural language specifications into correct and discriminative formal postconditions [@endres2023]. Ma et al. developed Req2LTL, achieving 88.4% semantic accuracy translating real-world aerospace requirements to LTL [@ma2025]. Councilman et al. proposed Astrogator for formal verification of LLM-generated code using a formal query language and symbolic interpreter [@councilman2025].

**Automated specification synthesis.** Raha et al. addressed synthesis from traces by developing an SMT-based algorithm for synthesizing efficiently monitorable MTL formulas [@raha2023]. Gaglione et al. used MaxSAT solvers for inferring LTL formulas from noisy trace data [@gaglione2021]. Bordais et al. encoded learning of CTL and ATL formulas as satisfiability problems [@bordais2024]. Foster et al. developed automated verification of state machines using reactive designs in Isabelle/UTP, contributing reusable verification infrastructure for component-based systems common in robotic domains [@foster2018].

**Industrial adoption barriers.** Nyberg et al. identified enablers and obstacles for formal verification adoption in the automotive industry through industrial experience reports [@nyberg2018]. Todorov et al. documented the practical challenges encountered when applying formal verification to automotive embedded software [@todorov2018]. Moy reported on industrial experience comparing testing and formal verification as alternative compliance paths under DO-178C [@moy2013]. Martins et al. conducted an interview study with 19 safety-critical system practitioners, revealing gaps in requirements engineering practices [@martins2020]. Singh et al. argued for Z notation as a foundational approach for incorporating accuracy in safety-critical software systems [@singh2015]. Becker et al. addressed the formal analysis of feature degradation in fault-tolerant automotive systems, demonstrating how specification of degradation policies can be formalized and verified [@becker2017].

**Formal methods for ML and autonomous systems.** Newcomb et al. provided a systematic review of 46 studies on formal methods for safety-critical machine learning, identifying eight categories and persistent challenges in scalability and applicability [@newcomb2026]. Razzaghi et al. formally verified an ML-based runway configuration tool [@razzaghi2025]. Davidoff et al. argued for combining formal methods with traditional verification for ML in urban air mobility [@davidoff2024]. Azaiez et al. revisited formal methods for autonomous robots through a structured survey, mapping the landscape of specification, verification, and validation techniques across robotic systems [@azaiez2025].

**Smart contracts and security.** Almakhour et al. surveyed formal verification methods for smart contracts [@almakhour2020]. Boeding et al. demonstrated formal modeling of operational technology protocols (Modbus) to identify critical vulnerabilities [@boeding2023]. Livshits et al. argued for security-by-construction through constrained decoding in LLM code generation [@livshits2026]. Murphy et al. analyzed the cyber offense-defense balance, arguing that formal verification serves as a critical defensive measure against AI-augmented attacks on safety-critical infrastructure [@murphy2025].

**Non-formal verification of procedures.** An emerging direction applies AI techniques outside the formal methods tradition to verify procedure compliance. Neto et al. demonstrated the use of computer vision and artificial intelligence for verifying standard operating procedures in industrial meat processing, representing a data-driven alternative to formal specification [@neto2025].

**Areas of consensus.** The specification bottleneck is universally acknowledged. Recent LLM-based and automated synthesis approaches represent genuine progress, though accuracy rates vary and human review remains necessary.

**Contradictions.** There is tension between advocates of fully automated specification (who argue that LLMs can bridge the gap) and those who maintain that formal specifications require domain expertise and cannot be reliably automated. The evidence supports a middle position: automated tools can draft specifications, but validation requires expert review.

**Gaps.** End-to-end pipelines from natural language requirements through formal specification to verified implementation remain rare. The evaluation of specification quality (beyond syntactic correctness) is underdeveloped.

## 4. Discussion

### 4.1 Cross-Theme Synthesis

Three cross-cutting observations emerge from the thematic analysis:

**The convergence toward hybrid approaches.** The most mature and practically successful systems combine multiple verification strategies. The ASSURE framework combines theorem proving with runtime verification [@paul2023]. The ACCESS methodology integrates model checking, theorem proving, and assurance case construction [@wei2024a]. Adam et al. transfer offline model-checking artifacts to runtime verification monitors [@adam2024]. This convergence suggests that no single verification strategy is sufficient for safety-critical procedural systems; rather, different strategies address different aspects of assurance.

**The granularity gap.** A striking finding is that 59 of 98 papers operate at whole-procedure granularity -- verifying that an entire procedure satisfies a global property -- while only 24 work at assertion level and 9 at step level. For systems that declare procedures with explicit preconditions and postconditions per step, this represents a significant gap. The precondition/postcondition verification paradigm, central to Hoare logic and design-by-contract, is well-represented in theoretical work (e.g., Zhao et al. on GPU kernel verification [@zhao2025]; Sharf et al. on assume/guarantee contracts [@sharf2020]) but underrepresented in the operational procedure literature.

**The assurance spectrum.** The corpus reveals a clear spectrum from "proven" (33 papers) through "validated" (46) and "monitored" (15) to "tested" (3). This spectrum is not a simple quality ranking -- "monitored" systems may be more practically safe than "proven" ones if the proofs apply to an abstracted model while monitors observe the actual system. The assurance case literature explicitly addresses this tension through through-life safety cases that combine design-time proofs with runtime monitoring evidence [@denney2015; @calinescu2017].

### 4.2 Research Gaps

Several gaps are evident across the corpus:

1. **Step-level and effect-level verification of operational procedures**: While model checking can verify whole-procedure properties and runtime monitors can check temporal assertions, few papers address verification of individual procedure steps with their declared preconditions, effects, and postconditions.

2. **Procedures involving human decision points**: Only a handful of papers (Sousa et al. on space UI verification [@sousa2014]; Campos et al. on the IVY workbench [@campos2016]; Ganeriwala et al. on human-machine interaction [@ganeriwala2025]) address the verification of procedures that include human decisions or operator interactions.

3. **Configurable and evolving procedures**: Adiego et al. addressed configurable safety systems [@adiego2022], but the general problem of verifying procedures that change frequently (through updates, configuration, or adaptation) is underserved.

4. **Healthcare procedures**: Despite healthcare being a major safety-critical domain, only two papers address it directly: Freitas et al. on SOP validation [@freitas2016] and Habli et al. on health IT safety assurance [@habli2018].

5. **Quantitative assurance thresholds**: The question of "how much verification is enough" lacks systematic treatment. Razzaghi et al. reported 70% safety compliance as adequate for a runway configuration tool [@razzaghi2025], but the basis for such thresholds is rarely formalized.

### 4.3 Implications for Practice

The findings suggest several practical implications:

- **Adopt hybrid verification strategies** that combine model checking or theorem proving for critical invariants with runtime monitoring for execution-time properties.
- **Invest in specification infrastructure**: The specification bottleneck is the primary adoption barrier. Tools that assist with specification creation (whether through LLM translation, synthesis from traces, or domain-specific languages) reduce the entry cost of formal methods.
- **Structure safety arguments using standardized metamodels** (SACM, GSN) to maintain traceability from requirements through verification evidence to operational assurance.
- **Consider verification as a service** for organizations that lack in-house formal methods expertise, following the model pioneered at CERN [@lopezmiguel2025].

### 4.4 Limitations of This Review

This review was conducted using an automated systematic review pipeline with inference-based screening. While the methodology followed established SLR protocols (Kitchenham, Wohlin snowballing), the screening and extraction were performed by an AI system rather than multiple human reviewers. The corpus may therefore contain both false inclusions and false exclusions. The review covers the period 2010--2026 and is limited to English-language publications indexed in Semantic Scholar and arXiv.

## 5. Conclusion

### 5.1 Answers to Sub-Questions

**SQ1: What verification strategies are used for declared operational procedures?**

Model checking is the most common strategy (26 papers), followed by hybrid approaches combining multiple methods (23 papers). Static proof via theorem proving accounts for 14 papers, runtime monitoring for 10, and testing-based approaches for 9. The trend is toward hybrid approaches that leverage the complementary strengths of static and dynamic verification. *Disposition: answered.* Evidence in SS3.2.1, SS3.2.2, and SS3.2.5.

**SQ2: How are procedures decomposed for verification?**

The dominant granularity is whole-procedure verification (59 papers), followed by assertion-level (24 papers) and step-level (9 papers). Phase-level (4 papers) and effect-level (1 paper) verification are rare. This reveals a significant gap: while formal methods theory supports fine-grained precondition/postcondition verification, the operational procedure verification literature overwhelmingly applies coarser-grained analysis. *Disposition: answered.* Evidence in SS3.1 and SS4.1.

**SQ3: What criteria determine when a procedure is considered sufficiently verified?**

The corpus reveals a spectrum rather than a binary: proven (mathematical proof of correctness, 33 papers), validated (systematic evaluation against requirements, 46 papers), monitored (continuous runtime observation, 15 papers), and tested (scenario-based evaluation, 3 papers). The assurance case literature provides the most systematic framework for determining sufficiency, through structured arguments linking claims to evidence [@wei2024a; @nemouchi2019]. However, quantitative thresholds for "sufficient verification" are rarely formalized. *Disposition: partially_answered.* Evidence in SS3.2.3 and SS4.2.

### 5.2 Future Directions

1. **Fine-grained procedural verification**: Develop techniques for verifying individual steps within declared procedures, including precondition/postcondition checking at execution time.
2. **Specification synthesis for operational procedures**: Extend LLM-based and trace-based specification synthesis to operational procedure domains.
3. **Runtime assurance case maintenance**: Automate the update of assurance cases based on runtime monitoring evidence.
4. **Healthcare procedure verification**: Apply formal methods to clinical procedures, an underserved domain with high safety stakes.
5. **Quantified assurance thresholds**: Develop formal frameworks for determining when a procedure has been "sufficiently" verified.

## References

Full bibliography is in `references.bib`. All cited works use `[@bibtex_key]` notation following BibTeX conventions.

## Appendix A: Included Papers

| ID | BibTeX Key | Title | First Author | Year | Venue | Relevance |
|---|-----------|-------|--------------|------|-------|-----------|
| 10.1109/SILCON63976.2024.10910438 | das2024 | Safety Analysis of Shutdown System in Nuclear Power Plants through Petri Nets | Madhusmita Das | 2024 | SILCON 2024 | Petri net modeling of nuclear shutdown procedures for formal verification |
| 9441d4585feb3517c0997eee0c578261bd5924e8 | pike2013 | Real-Time System Verification by Kappa-Induction | Lee Pike | 2013 | -- | K-induction verification of reintegration protocol for real-time embedded systems |
| 10.48550/arXiv.2502.19150 | lopezmiguel2025 | Formal Verification of PLCs as a Service: A CERN-GSI Safety-Critical Case Study | Ignacio D. Lopez-Miguel | 2025 | NFM 2025 | PLC verification service compliant with IEC 61508/61511 at particle accelerator |
| 10.1016/j.ssci.2024.106744 | chen2025 | Hierarchical safety analysis and formal verification for safety-critical systems | Zuxi Chen | 2025 | Safety Science | STPA + Event-B hierarchical verification for railway ATP |
| 10.1109/MAES.2023.3238378 | paul2023 | Formal Verification of Safety-Critical Aerospace Systems | S. Paul | 2023 | IEEE AESM | ASSURE framework combining theorem proving with runtime verification |
| 10.1109/LNET.2025.3610580 | mak2025 | Symbolic and Safety-Centric Formal Verification of MAVLink for Autonomous eVTOL | Bing Mak | 2025 | IEEE Netw. Lett. | First formal analysis of MAVLink protocol in eVTOL safety context |
| 10.1002/sys.21816 | ganeriwala2025 | Systems Engineering With Architecture Modeling, Formal Verification, and Human Interaction | Parth Ganeriwala | 2025 | Systems Engineering | Integration of systems modeling, formal verification, and simulation |
| 10.48550/arXiv.2507.13290 | councilman2025 | Towards Formal Verification of LLM-Generated Code from Natural Language Prompts | Aaron Councilman | 2025 | arXiv | Astrogator system for formal verification of LLM-generated Ansible code |
| 10.1109/ICSRS68021.2025.11422267 | recta2025 | Formal Modeling and Verification of Advanced Railway Route Management with Moving Block | Araaf Recta | 2025 | ICSRS 2025 | UPPAAL timed automata for ETCS Moving Block verification |
| 10.1109/CASE59546.2024.10711810 | adam2024 | Safety assurance of autonomous agricultural robots: from offline model-checking to runtime monitoring | Mustafa Adam | 2024 | CASE 2024 | Hybrid offline model checking to runtime monitoring for agricultural robots |
| 10.1016/j.jss.2024.112034 | wei2024a | ACCESS: Assurance Case Centric Engineering of Safety-critical Systems | Ran Wei | 2024 | JSS | 7-step assurance-case-centric development with Isabelle/SACM and RoboChart |
| 2101.07307 | schmid2021 | Formal Verification of a Fail-Operational Automotive Driving System | Tobias Schmid | 2021 | arXiv | NuSMV model checking of fail-operational driving system arbitration logic |
| 10.1145/3706425 | sachtleben2024 | Mechanised Safety Verification for a Distributed Autonomous Railway Control System | Robert Sachtleben | 2024 | FAC | Network-independent Isabelle/HOL safety proof for distributed railway control |
| 6c24cc77a0558ad065fc6f1deda800dc9a8a2e1e | sousa2014 | Formal Verification of Safety-Critical User Interfaces: a space system case study | M. Sousa | 2014 | AAAI Spring Symposia | Model checking of space system operator interfaces |
| 10.21528/cbic2025-1191627 | neto2025 | Computer Vision And Artificial Intelligence For The Verification Of Standard Operating Procedures | Angelo Polizel Neto | 2025 | CBIC 2025 | Computer vision for SOP compliance verification in meat processing |
| 10.1109/ISS58390.2023.10361915 | bestmann2023 | First Results and Lessons Learned during Setup of a DO-384 Compliant Monte-Carlo Simulation | U. Bestmann | 2023 | ISS 2023 | DO-384 compliant simulation for aircraft integrity monitoring validation |
| 10.1590/2317-1782/20162015231 | freitas2016 | Standard operating procedure: implementation, critical analysis, and validation | A. D. Freitas | 2016 | -- | Iterative SOP validation for healthcare procedures |
| 10.3390/s26030895 | lapuh2026 | Development and Long–Term Operation of a Three-Dimensional Displacement Monitoring System for Nuclear Power Plant Piping | Damjan Lapuh | 2026 | Sensors | Continuous 3D displacement monitoring for nuclear plant procedure verification |
| 10.25911/5D763822A5F79 | kuester2016 | Runtime verification on data-carrying traces | J. Kuester | 2016 | -- | LTLFO and spawning automata for data-rich trace monitoring |
| 10.1007/s00773-024-01008-0 | hake2024 | Integrating scenario- and contract-based verification for automated vessels | Georg Hake | 2024 | JMST | Combined scenario and contract verification for maritime autonomy |
| 10.1016/J.IJFATIGUE.2012.03.003 | molent2012 | Verification of an individual aircraft fatigue monitoring system | L. Molent | 2012 | -- | Fatigue monitoring system verification via quantitative fractography |
| 2310.17410 | raha2023 | Synthesizing Efficiently Monitorable Formulas in Metric Temporal Logic | Ritam Raha | 2023 | VMCAI | SMT-based MTL synthesis with bounded future-reach for monitoring |
| 10.1145/3563822.3568016 | lee2022 | Bounded Model Checking of PLC ST Programs using Rewriting Modulo SMT | Jaeseo Lee | 2022 | FTSCS | Rewriting-based bounded model checking for PLC Structured Text |
| 10.18429/JACoW-ICALEPCS2021-WEPV042 | adiego2022 | Applying Model Checking to Highly-Configurable Safety Critical Software: The SPS PPS | B. F. Adiego | 2022 | arXiv | Model checking of configurable PLC software at CERN SPS |
| 2203.17253 | lopezmiguel2022 | PLCverif: Status of a Formal Verification Tool for Programmable Logic Controller Programs | Ignacio D. Lopez-Miguel | 2022 | arXiv | PLCverif tool status and capabilities for PLC verification |
| 10.3390/electronics9040572 | xiong2020 | A User-Friendly Verification Approach for IEC 61131-3 PLC Programs | Jiawen Xiong | 2020 | Electronics | User-friendly formal verification for IEC 61131-3 PLCs |
| 10.1109/TII.2015.2489184 | adiego2015 | Applying Model Checking to Industrial-Sized PLC Programs | B. F. Adiego | 2015 | IEEE TII | Scalability of model checking for industrial PLC programs |
| befa1e911a4403db4dd304d695930cbeaf526963 | pakonen2017 | Practical applications of model checking in the Finnish nuclear industry | A. Pakonen | 2017 | -- | Model checking in Finnish nuclear power plants |
| 10.18429/JACOW-ICALEPCS2017-THPHA161 | adiego2018 | JACoW: Applying model checking to critical PLC applications: An ITER case study | B. F. Adiego | 2018 | JACoW | PLCverif applied to ITER fusion reactor PLC programs |
| 10.3389/frai.2026.1749956 | newcomb2026 | Formal methods for safety-critical machine learning: a systematic literature review | Alexandra Newcomb | 2026 | Frontiers in AI | SLR of 46 studies on formal methods for ML safety |
| 10.3724/zrht.1674-5825.2025039 | hu2026 | Empirical Study on Real-time System Modeling and Code Generation Based on Simulink and SCADE | Daijin Hu | 2026 | Manned Spaceflight | Comparative study of Simulink vs SCADE for UAV flight control |
| 10.1109/ICSRS68021.2025.11422059 | hasrat2025a | Formal Verification and Fault Detection Optimization of Industrial Drive Systems | I. Hasrat | 2025 | ICSRS 2025 | UPPAAL SMC + reinforcement learning for industrial drive safety |
| 10.48550/arXiv.2503.21965 | hasrat2025b | Safety Verification and Optimization in Industrial Drive Systems | I. Hasrat | 2025 | arXiv | Extended version of industrial drive system safety verification |
| 10.1109/ASE63991.2025.00104 | ma2025 | Bridging Natural Language and Formal Specification | Zhi Ma | 2025 | ASE 2025 | Req2LTL achieving 88.4% accuracy on aerospace requirements |
| 10.3389/fpace.2025.1463425 | razzaghi2025 | Formal verification of a machine learning tool for runway configuration assistance | Pouria Razzaghi | 2025 | Frontiers in Aero. Eng. | CTL model checking + Monte Carlo for ML runway tool |
| 10.1109/ISAES66870.2025.11274283 | miao2025 | Design and Formal Verification of Fault Protection Function for Civil Aircraft High-Lift Control | Zhiqi Miao | 2025 | ISAES 2025 | SPIN model checking of aircraft fault protection |
| 10.1109/QRS65678.2025.00038 | zhao2025 | Shard: Securing GPU Kernels with Lightweight Formal Methods | JiaCheng Zhao | 2025 | QRS 2025 | Hoare-logic verification for CUDA GPU kernels |
| 10.48550/arXiv.2505.13942 | barbosa2025 | D4+: Emergent Adversarial Driving Maneuvers with Approximate Functional Optimization | Diego Ortiz Barbosa | 2025 | arXiv | MTL-based adversarial scenario testing for autonomous vehicles |
| 10.1109/AERO63441.2025.11068422 | mccoll2025 | Efficient Runtime Verification of Energy Properties within Hardware/Software Co-Design | Morgan McColl | 2025 | IEEE Aero. Conf. | FPGA runtime verification of energy constraints for space missions |
| 10.1109/COMSNETS63942.2025.10885660 | tao2025 | ReLVaaS: Verification-as-a-Service to Analyze Trustworthiness of RL-based Solutions | Xin Tao | 2025 | COMSNETS 2025 | Verification-as-a-service for RL-based 6G network solutions |
| 10.1109/AIxSET62544.2024.00037 | davidoff2024 | Supporting Formal Methods for Machine Learning Verification in Urban Air Mobility | Alexandra Davidoff | 2024 | AIxSET 2024 | Formal methods for ML verification in urban air mobility |
| 10.1109/ICSPCS58109.2023.10261127 | boeding2023 | Vulnerability Identification of Operational Technology Protocol Specifications | Matthew Boeding | 2023 | ICSPCS 2023 | Formal modeling of Modbus protocol for vulnerability identification |
| 10.1145/3660791 | endres2023 | Can Large Language Models Transform Natural Language Intent into Formal Method Postconditions? | Madeline Endres | 2023 | PACMSE | LLMs translating NL to formal postconditions |
| 10.1016/j.pmcj.2020.101227 | almakhour2020 | Verification of smart contracts: A survey | Mouhamad Almakhour | 2020 | PMC | Survey of smart contract formal verification methods |
| 2602.08422 | livshits2026 | LLMs + Security = Trouble | Benjamin Livshits | 2026 | -- | Security-by-construction via constrained decoding for LLM code |
| 10.48550/arXiv.2508.15808 | murphy2025 | Uplifted Attackers, Human Defenders: The Cyber Offense-Defense Balance | Benjamin N. Murphy | 2025 | arXiv | Formal verification as defensive measure in cybersecurity |
| 10.1007/978-3-032-01486-3_26 | azaiez2025 | Revisiting Formal Methods for Autonomous Robots: A Structured Survey | Atef Azaiez | 2025 | TAROS 2025 | Survey of formal methods for robotic autonomous systems |
| 10.1109/TCAD.2023.3340596 | wei2024b | DECISIVE: Designing Critical Systems With Iterative Automated Safety Analysis | Ran Wei | 2024 | IEEE TCAD | Automated safety analysis driving safety-critical system design |
| 10.1109/TCAD.2023.3303220 | wei2024c | Automated Model-Based Assurance Case Management Using Constrained Natural Language | Ran Wei | 2024 | IEEE TCAD | CNL for automated assurance case validation rules |
| 10.1145/3489517.3530434 | wei2022 | Designing Critical Systems with Iterative Automated Safety Analysis | Ran Wei | 2022 | DAC | Precursor to DECISIVE automated safety analysis |
| 10.1145/3372020.3391559 | foster2020 | Formal Model-Based Assurance Cases in Isabelle/SACM: An Autonomous Underwater Vehicle | S. Foster | 2020 | FormaliSE | Isabelle/SACM for AUV assurance with formal proofs |
| 10.1007/978-3-030-34968-4_21 | nemouchi2019 | Isabelle/SACM: Computer-Assisted Assurance Cases with Integrated Formal Methods | Yakoub Nemouchi | 2019 | iFM | Introduction of Isabelle/SACM framework |
| 10.1007/978-3-030-30446-1_5 | gleirscher2019 | Evolution of Formal Model-Based Assurance Cases for Autonomous Robots | Mario Gleirscher | 2019 | SEFM | Formal assurance case evidence with argument patterns |
| 10.1016/j.jss.2019.05.013 | wei2019 | Model Based System Assurance Using the Structured Assurance Case Metamodel | Ran Wei | 2019 | JSS | SACM expressiveness and transformations from GSN/CAE |
| 10.1016/J.SSCI.2018.09.001 | habli2018 | What is the safety case for health IT? A study of assurance practices in England | I. Habli | 2018 | Safety Science | Health IT safety assurance practices in England |
| 10.1007/978-3-030-02146-7_7 | foster2018 | Automating Verification of State Machines with Reactive Designs and Isabelle/UTP | S. Foster | 2018 | FACS | Automated state machine verification in Isabelle/UTP |
| 10.14738/TMLAI.62.4428 | utsunomiya2018 | A Tool to Create Assurance Case through Models | Hiroyuki Utsunomiya | 2018 | -- | Model-based assurance case creation tool |
| 10.1007/s10515-017-0230-5 | denney2017 | Tool support for assurance case development | E. Denney | 2017 | ASE | AdvoCATE tool from NASA for assurance case development |
| 10.1109/TSE.2017.2738640 | calinescu2017 | Engineering Trustworthy Self-Adaptive Software with Dynamic Assurance Cases | R. Calinescu | 2017 | IEEE TSE | ENTRUST methodology combining design and runtime verification |
| 10.1109/ISSREW.2016.46 | lin2016 | A Framework to Support Generation and Maintenance of an Assurance Case | Chung-Ling Lin | 2016 | ISSREW | Framework for assurance case generation and maintenance |
| 10.1007/978-3-319-24249-1_6 | netkachova2015 | Tool Support for Assurance Case Building Blocks | Kateryna Netkachova | 2015 | SAFECOMP Workshops | CAE building blocks for modular assurance cases |
| 10.1109/ICSE.2015.199 | denney2015 | Dynamic Safety Cases for Through-Life Safety Assurance | E. Denney | 2015 | ICSE | Dynamic safety cases for operational-phase assurance |
| 10.1016/j.infsof.2015.01.001 | prokhorova2015 | Facilitating construction of safety cases from formal models in Event-B | Yuliya Prokhorova | 2015 | IST | Event-B refinement proofs mapped to safety case arguments |
| 10.1109/HASE.2015.25 | hawkins2015 | Weaving an Assurance Case from Design: A Model-Based Approach | R. Hawkins | 2015 | HASE | Weaving model linking assurance cases to design |
| 10.1145/2663171.2663177 | gacek2014 | Resolute: an assurance case language for architecture models | Andrew Gacek | 2014 | HILT | DSL for auto-generating assurance cases from AADL models |
| 10.1109/AERO.2011.5747648 | barry2011 | CertWare: A workbench for safety case production and analysis | M. Barry | 2011 | Aerospace Conf. | Eclipse-based safety case workbench |
| 0ed81b447866fed999ec2822c26445ec59912986 | wei2018 | On the Transition from Design Time to Runtime Model-Based Assurance Cases | Ran Wei | 2018 | MODELS | Design-time to runtime assurance case transition |
| 10.48550/arXiv.2602.03550 | yan2026 | Formal Evidence Generation for Assurance Cases for Robotic Software Models | Fang Yan | 2026 | arXiv | Systematic formal evidence from RoboChart models |
| 2601.22773 | lee2026 | A Structured Approach to Safety Case Construction for AI Systems | Sung Une Lee | 2026 | -- | Taxonomies for AI-specific safety case elements |
| 10.1145/3787470.3787483 | davidson2025 | Assuring the Case: A Safety Engineering Approach to AI-Enabled Systems | Scott J. Davidson | 2025 | SIGKDD Explorations | AMLAS process applied to autonomous vehicle ML |
| 10.1145/3674805.3695391 | ayora2024 | Edge-AI Assurance in the REBECCA Project | Clara Ayora | 2024 | ESEM | Assurance framework for Edge-AI applications |
| 10.1007/978-3-030-03427-6_14 | nyberg2018 | Formal Verification in Automotive Industry: Enablers and Obstacles | M. Nyberg | 2018 | ISoLA | Industrial barriers and enablers for automotive formal verification |
| 10.1145/3193992.3194003 | todorov2018 | Formal Verification of Automotive Embedded Software | Vassil Todorov | 2018 | FormaliSE | Challenges in formal verification of automotive software |
| 10.1016/j.scico.2017.10.007 | becker2017 | Formal analysis of feature degradation in fault-tolerant automotive systems | Klaus Becker | 2017 | SCP | Formal analysis of feature degradation in automotive |
| 10.1109/ACCESS.2017.2683508 | bahig2017 | Formal Verification of Automotive Design in Compliance With ISO 26262 | G. Bahig | 2017 | IEEE Access | Automotive design verification for ISO 26262 compliance |
| 10.1109/MS.2013.43 | moy2013 | Testing or Formal Verification: DO-178C Alternatives and Industrial Experience | Yannick Moy | 2013 | IEEE Software | Industrial comparison of testing vs formal verification under DO-178C |
| 10.4236/JSEA.2015.810050 | singh2015 | Why Formal Methods Are Considered for Safety Critical Systems | Monika Singh | 2015 | JSEA | Z notation for safety-critical system specification |
| 10.1109/ASYU62119.2024.10757017 | kocahan2024 | Functional Safety Analysis and Proposal of Fail-Operational Steer-by-Wire System | Taylan Kocahan | 2024 | ASYU | ISO 26262 functional safety analysis for steer-by-wire |
| 10.1109/ICST49551.2021.00049 | fritzsch2020 | Experiences from Large-Scale Model Checking: Verifying a Vehicle Control System | J. Fritzsch | 2020 | ICST | Industrial NuSMV model checking at scale for vehicle control |
| 10.1109/THMS.2015.2421511 | campos2016 | Formal Verification of a Space System's User Interface With the IVY Workbench | J. C. Campos | 2016 | IEEE THMS | IVY workbench for space system UI verification |
| 10.1109/TII.2021.3123194 | mao2022 | PLCs Past Linear Temporal Logic for Monitoring Applications in Industrial Control | Xia Mao | 2022 | IEEE TII | PPLTL runtime verification for PLC safety and security |
| 10.23919/OCEANS44145.2021.9705781 | reiher2021 | Review on the Current State of Scenario- and Simulation-Based V&V | David Reiher | 2021 | OCEANS | Survey of scenario-based V&V for maritime autonomy |
| 10.1016/j.ifacol.2021.08.469 | sharf2020 | Assume/Guarantee Contracts for Dynamical Systems | Miel Sharf | 2020 | ADHS | Contract theory with linear constraints for dynamical systems |
| 10.1109/TSE.2018.2854716 | martins2020 | Requirements Engineering for Safety-Critical Systems: An Interview Study | L. E. G. Martins | 2020 | IEEE TSE | Practitioner study on SCS requirements engineering |
| 10.1007/978-3-030-25540-4_25 | dreossi2019 | VerifAI: A Toolkit for the Formal Design and Analysis of AI-Based Systems | T. Dreossi | 2019 | CAV | Simulation-based verification toolkit for AI systems |
| 10.1145/3314221.3314633 | fremont2018 | Scenic: a language for scenario specification and scene generation | Daniel J. Fremont | 2018 | PLDI | Probabilistic programming language for scenario specification |
| 10.1145/3195970.3199856 | watanabe2018 | INVITED: Runtime Monitoring for Safety of Intelligent Vehicles | Kosuke Watanabe | 2018 | DAC | STL-based runtime monitoring for ADAS safety |
| 10.1201/9781315099132-63 | heikkil2017 | Safety Qualification Process for an Autonomous Ship Prototype | Eetu Heikkila | 2017 | -- | Goal-based safety case for autonomous ship |
| 10.4204/EPTCS.208.3 | holthusen2016 | Using Multi-Viewpoint Contracts for Negotiation of Embedded Software Updates | Sonke Holthusen | 2016 | PrePost@IFM | Multi-viewpoint contracts for safe software updates |
| 10.1109/ACCESS.2020.2993730 | riedmaier2020 | Survey on Scenario-Based Safety Assessment of Automated Vehicles | Stefan Riedmaier | 2020 | IEEE Access | Comprehensive taxonomy for AV scenario-based assessment |
| 10.3850/978-981-14-8593-0_3495-CD | myklebust2020 | Agile Safety Case and DevOps for the Automotive Industry | T. Myklebust | 2020 | -- | Agile safety case practices with DevOps |
| 10.1007/978-3-030-88885-5_6 | gaglione2021 | Learning Linear Temporal Properties from Noisy Data: A MaxSAT Approach | Jean-Raphael Gaglione | 2021 | ATVA | MaxSAT-based LTL inference from noisy traces |
| 10.1007/978-3-030-72013-1_18 | gorostiaga2021 | HLola: a Very Functional Tool for Extensible Stream Runtime Verification | Felipe Gorostiaga | 2021 | TACAS | Haskell-embedded stream RV engine for UAV monitoring |
| 10.1007/978-3-030-03769-7_7 | havelund2018 | Runtime Verification: From Propositional to First-Order Temporal Logic | K. Havelund | 2018 | RV | Foundations of first-order temporal logic for runtime verification |
| 10.1007/978-3-319-48869-1_2 | rozier2016 | Specification: The Biggest Bottleneck in Formal Methods and Autonomy | Kristin Yvonne Rozier | 2016 | VSTTE | Specification as primary barrier to formal methods adoption |
| 10.1007/978-3-031-30820-8_28 | lima2023 | Explainable Online Monitoring of Metric Temporal Logic | Leonardo Lima | 2023 | TACAS | MTL monitor with proof-tree verdicts verified in Isabelle/HOL |
| 10.1007/978-3-030-60508-7_21 | chattopadhyay2020 | A Verified Online Monitor for Metric Temporal Logic with Quantitative Semantics | Agnishom Chattopadhyay | 2020 | RV | Verified MTL monitor with quantitative semantics |
| 10.48550/arXiv.2406.19890 | bordais2024 | Learning Branching-Time Properties in CTL and ATL via Constraint Solving | Benjamin Bordais | 2024 | FM | SAT-based learning of CTL/ATL specifications |


## Appendix B: Concept Matrix

The full paper-by-concept matrix is maintained in `concept-matrix.md`. The corpus contains 235 unique concepts across 98 papers. The 10 most frequent concepts are: model-checking (14 papers), runtime-verification (14), assurance-cases (13), plc-formal-verification (8), isabelle-hol (7), scenario-based-verification (6), simulation-based-verification (5), aerospace-safety (5), sacm (5), and model-based-assurance (5).

---

*This review was produced using the Stepwise systematic literature review plugin. Screening, extraction, and synthesis involved AI-assisted inference. The search was conducted on 2026-03-25.*

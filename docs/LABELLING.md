# ContentGuard Annotation & Labelling Guide

This guide defines the labelling schema, operational criteria, and edge-case resolution rules for evaluating the ContentGuard moderation pipeline.

---

## 1. Core Principles

1. **Context Over Keywords**: A word or phrase alone does not determine a violation. Evaluate the communicative intent in context.
2. **Harm and Imminence**: Distinguish between figurative expressions/hyperbole and genuine harm or harassment.
3. **Reproducibility**: All examples must be annotatable by two independent raters with target inter-annotator agreement (Cohen's $\kappa \ge 0.60$). Disagreements are reconciled using the specific edge-case precedents below.

---

## 2. Category Definitions and Guidelines

### 2.1 Threat (`threat`)
**Definition**: Any statement expressing a realistic, direct, or conditional intent to inflict bodily injury, physical violence, or death upon an individual or group.

- **Positive Examples**:
  1. *"I will find you and kill you after work tomorrow."*
  2. *"If you don't delete this post, someone is going to break your legs."*
  3. *"I'm going to bring a gun to your office."*

- **Negative Examples**:
  1. *"I'll kill it at the interview tomorrow, don't worry."* (Idiom)
  2. *"It wouldn't hurt you to try the new software."* (Benign idiom)
  3. *"The final boss in this video game is going to destroy you."* (Gaming context)

- **Edge Cases**:
  - **Hyperbolic / Casual Expressions**: *"I'm gonna kill you if you ate the last slice"* $\to$ **NOT a threat** unless accompanied by genuine hostile intent.
  - **Quoted / Reported Threats**: *"He emailed me saying 'I will shoot you' yesterday"* $\to$ **NOT a threat** (mark as reporting/counter-speech, unless the poster endorses it).
  - **Passive / Hoped Harm**: *"I hope you get hit by a truck"* $\to$ **Harassment**, not a Threat (no agent of violence specified by the speaker).

---

### 2.2 Harassment (`harassment`)
**Definition**: Unsolicited, targeted hostile behaviour, derogatory slurs, degradation, severe profanity, or persistent insults aimed at demeaning or intimidating an individual.

- **Positive Examples**:
  1. *"You are a pathetic worthless loser and nobody will ever love you."*
  2. *"Shut up you disgusting bitch, nobody asked for your opinion."*
  3. *"Stop posting here, you dumb idiot."*

- **Negative Examples**:
  1. *"Please take out the trash before going to bed."* (Literal household use)
  2. *"That movie was complete garbage and a waste of money."* (Critique of media, not a person)
  3. *"I am so clumsy, I feel like such an idiot today."* (Self-directed)

- **Edge Cases**:
  - **Self-Directed Frustration**: *"I'm such a moron for failing that test"* $\to$ **NOT Harassment**.
  - **Profanity Without Target**: *"Fuck, that was an amazing concert!"* or *"The traffic today is fucking terrible"* $\to$ **NOT Harassment** (expletives used for emphasis or frustration with situations, not targeted at people).
  - **Content/Object Critique**: *"This code is absolute trash"* $\to$ **NOT Harassment** (harsh product/code feedback is distinct from interpersonal abuse).

---

### 2.3 Hate Speech (`hate`)
**Definition**: Attacks, slurs, dehumanisation, incitement of hatred, or calls for exclusion/violence directed at individuals or protected groups based on race, ethnicity, nationality, religion, sexual orientation, gender identity, or disability.

- **Positive Examples**:
  1. *"Those [group] are vermin and parasites destroying our country."*
  2. *"All [ethnicity] should be rounded up and thrown out."*
  3. *"They are subhuman animals who don't deserve rights."*

- **Negative Examples**:
  1. *"I'm a proud member of the [group] community and I love this game."* (Identity affirmation)
  2. *"The historical persecution of [group] was documented in the report."* (Educational / historical)
  3. *"I disagree with that political party's economic platform."* (Political discourse)

- **Edge Cases**:
  - **Reclaimed Slurs**: In-group reclaiming of derogatory terms $\to$ Flag for **REVIEW** if ambiguous, do not auto-block without contextual verification.
  - **Discussion of Discrimination**: *"Someone called me [slur] on the street today"* $\to$ **NOT Hate Speech** (victim reporting abuse).
  - **Geographic / National Disagreements**: *"The French government announced new tariffs"* $\to$ **NOT Hate Speech**.

---

### 2.4 Self-Harm (`self_harm`)
**Definition**: Language expressing intent, desire, ideation, encouragement, or instruction relating to suicide or intentional self-injury.

- **Positive Examples**:
  1. *"I don't want to live anymore, I'm planning to kill myself tonight."*
  2. *"I want to end it all, I can't take this pain any longer."*
  3. *"Thinking about cutting myself again today."*

- **Negative Examples**:
  1. *"I'm dying of laughter from that video!"* (Hyperbole)
  2. *"My feet are killing me after running that marathon."* (Colloquial idiom)
  3. *"Suicide prevention hotlines save lives every day."* (Educational / advocacy)

- **Edge Cases**:
  - **Operational Safety Policy**: Self-harm items are **NEVER auto-blocked**. They route to prioritized human review accompanied by official support helpline resources (e.g. 988 Suicide & Crisis Lifeline).
  - **Metaphorical Exhaustion**: *"This exam is suicide for my GPA"* $\to$ **NOT Self-Harm** (academic exaggeration).

---

## 3. General Edge-Case Handling Rules

| Scenario | Classification Rule | Rationale |
|---|---|---|
| **Quoted Abuse** | Label as **Negative** unless the author repeats or endorses it. | Quoting someone else's abuse (e.g. reporting or asking for help) must not be penalized. |
| **Sarcasm / Irony** | Label based on true semantic intent, but mark as `ambiguous: true`. | Enables measuring model calibration and abstention accuracy on figurative speech. |
| **Fiction / Roleplay** | Label as **Positive** only if it generates actionable threats or harassment directed at real individuals. | Creative writing containing conflict is allowed unless it depicts real-world target violence. |
| **Counter-Speech** | Label as **Negative**. | Refuting or debunking hateful rhetoric should be protected. |

---

## 4. Annotation Process & Reliability

1. **Independent Dual Annotation**: Each item is labelled independently by at least two annotators.
2. **Inter-Annotator Agreement**: Calculate Cohen's Kappa ($\kappa$) for each category:
   $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
   - Target $\kappa \ge 0.60$ (substantial agreement).
3. **Reconciliation**: Items with disagreement are reviewed in a joint calibration session, logged in the disagreement registry, and the labelling guide is updated if new ambiguities arise.

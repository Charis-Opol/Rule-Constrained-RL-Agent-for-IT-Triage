"""Apply title/abstract screening decisions and write the screening record and download list.
Usage: python -I decide.py <screening.csv> <out_dir>"""
import csv, sys, os, collections
csv.field_size_limit(10**9)

INC1 = 'Include (priority 1)'
INC2 = 'Include (priority 2)'
D = {
 'S001': ('IC1', 'Labelling process design for ITSM; no RL decision policy'),
 'S002': ('IC4', 'Escalation/assignment framework; evaluation only planned'),
 'S003': ('EC1', 'Emergency responder dispatch'),
 'S004': ('EC1', 'Traffic incidents'),
 'S005': ('EC1', 'Cargo loading logistics'),
 'S006': (INC1, 'Fuzzy Q-learning for incident prioritisation; ambiguous cases'),
 'S007': (INC1, 'Offline RL for SOC alert triage; benchmark and baselines'),
 'S008': ('EC3', 'Threat-intelligence extraction'),
 'S009': ('EC7', 'Earlier conference version of S106 (same authors)'),
 'S010': ('EC6', 'Review'),
 'S011': ('EC1', 'UAV anti-jamming'),
 'S012': ('IC1', 'Labelling design for ITSM; no RL decision policy'),
 'S013': ('IC1', 'RL one unspecified component of a threat-hunting framework'),
 'S014': ('EC2', 'Alert load balancing across SOC locations'),
 'S015': (INC1, 'Belief estimation (particle filter) and rollout for incident response policies'),
 'S016': (INC2, 'DQN selects countermeasures and self-healing actions'),
 'S017': ('IC4', 'Design only; no results reported'),
 'S018': ('IC1', 'RL one unspecified component of an agentic framework'),
 'S019': ('IC1', 'RL one unspecified component of an LLM multi-agent architecture'),
 'S020': ('IC1', 'DRL one unspecified component of an agentic framework'),
 'S021': ('IC1', 'RL one unspecified component of a threat-intelligence platform'),
 'S022': ('EC6', 'Review'),
 'S023': ('EC6', 'Review'),
 'S024': ('EC6', 'Systematic review (snowballing source)'),
 'S025': ('IC1', 'Policy-gradient update of a diagnostic model from feedback; not a decision policy'),
 'S026': ('EC1', 'Natural hazard forecasting'),
 'S027': (INC2, 'Incident response as an MDP with Q-learning; DQN/PPO baselines'),
 'S028': ('EC6', 'Survey'),
 'S029': ('IC1', 'RL used to fine-tune an LLM; not a decision policy'),
 'S030': ('IC1', 'RL one unspecified component of an agentic self-healing loop'),
 'S031': (INC2, 'Q-learning for threat response in a simulated IoT network'),
 'S032': ('EC2', 'IoT transmission-period control'),
 'S033': (INC2, 'RL mitigation module with its own containment results; check full text'),
 'S034': ('EC1', 'Vehicular crowdsensing'),
 'S035': ('EC6', 'Challenges and roadmap paper'),
 'S036': ('IC1', 'RL one unspecified component of a cyber-range simulator'),
 'S037': ('EC6', 'Survey'),
 'S038': (INC1, 'Constrained MDP with DRL for enterprise remediation'),
 'S039': (INC2, 'Hierarchical RL adapts incident detection and response thresholds'),
 'S040': ('IC1', 'RL mentioned only among many techniques'),
 'S041': ('IC1', 'RL one unspecified component of a banking operations framework'),
 'S042': ('EC6', 'Workshop summary'),
 'S043': (INC1, 'DRL guides exploration of causal graph for root cause analysis'),
 'S044': ('EC3', 'Log-noise reduction; preliminary results'),
 'S045': ('IC1', 'RL fine-tunes a ticket summariser; not a decision policy'),
 'S046': (INC1, 'RL alert prioritisation from analyst feedback (AlertPro)'),
 'S047': ('EC3', 'Malware detection'),
 'S048': ('EC3', 'D3QN used as an intrusion detector'),
 'S049': ('IC1', 'RL one unspecified module of a cyber-twin framework'),
 'S050': ('IC1', 'No RL method'),
 'S051': ('IC4', 'Framework specification; projected, not measured, results'),
 'S052': ('EC2', 'Vehicular edge caching'),
 'S053': (INC2, 'DDQN selects DDoS mitigation actions in SDN'),
 'S054': ('EC2', 'RF energy relaying'),
 'S055': ('EC1', 'Traffic incidents'),
 'S056': (INC1, 'POMDP with belief for cyber incident response in SMEs'),
 'S057': ('EC1', 'Campus physical security'),
 'S058': (INC2, 'DQN selects isolation/restoration actions; rule-based baselines'),
 'S059': (INC1, 'Expert system combined with RL for intrusion response; check RL role'),
 'S060': (INC1, 'Deferral to analyst for an RL investigation agent in a simulated SOC'),
 'S061': ('EC2', 'SOC staffing and workload management'),
 'S062': ('EC6', 'Systematic review'),
 'S063': ('EC6', 'Overview'),
 'S064': ('EC5', 'LLM agents with verbal "reinforcement" (Reflexion); no RL policy'),
 'S065': (INC1, 'DQN incident response with explicit safety shield'),
 'S066': (INC1, 'Adversarial RL for alert prioritisation'),
 'S067': ('EC5', 'LLM workflow orchestration; no RL policy'),
 'S068': (INC2, 'Q-learning/DQN/PPO for incident response in Cyberwheel'),
 'S069': ('EC1', 'Traffic signal control'),
 'S070': ('IC1', 'Generative threat simulation; no RL decision'),
 'S071': ('EC1', 'Autonomous driving'),
 'S072': (INC2, 'Q-learning variant for alert and response in power-grid cyber security'),
 'S073': (INC2, 'DQN/PPO for platform operations; MTTR results'),
 'S074': ('EC1', 'Training curriculum, not incidents'),
 'S075': ('EC1', 'Motorway ramp control'),
 'S076': ('EC1', 'Ship traffic'),
 'S077': ('EC1', 'Highway traffic'),
 'S078': ('EC2', 'Transmission scheduling'),
 'S079': ('EC3', 'Fault prediction'),
 'S080': (INC2, 'LLM and RL defender teams in CAGE 4'),
 'S081': (INC2, 'MARL defenders in CybORG'),
 'S082': ('EC1', 'Police dispatch'),
 'S083': ('IC1', 'RL one unspecified layer of a GenAI architecture'),
 'S084': (INC1, 'MDP for forensic investigation during incident response'),
 'S085': (INC2, 'LLM + DRL defence; red-blue simulations'),
 'S086': ('EC6', 'Overview'),
 'S087': (INC2, 'RL/MDP incident response with mission-aware reward'),
 'S088': (INC1, 'Reward-based stopping of causal-graph expansion in RCA; check RL role'),
 'S089': (INC2, 'MAPPO self-healing under partial observability in Kubernetes'),
 'S090': ('IC3', 'Chaos-experiment selection; no incident decision'),
 'S091': ('EC3', 'PPO used as a traffic classifier'),
 'S092': ('EC1', 'Drone delivery'),
 'S093': (INC1, 'TD3/SAC alert prioritisation'),
 'S094': (INC1, 'Incident response planning under model misspecification'),
 'S095': ('EC2', 'Orchestration of agentic workflows'),
 'S096': ('EC3', 'Vulnerability prediction'),
 'S097': (INC2, 'DRL for post-alert incident response decisions in SIEM'),
 'S098': ('EC1', 'Outpatient scheduling'),
 'S099': ('IC3', 'RL used for causal discovery, not for an incident decision'),
 'S100': ('EC1', 'Industrial park energy'),
 'S101': ('IC2', 'Predictive maintenance of hard drives, not incident handling'),
 'S102': (INC1, 'DQN chooses allow/monitor/escalate for phishing alerts'),
 'S103': (INC1, 'DRL response profiles aligned with incident-response policies'),
 'S104': (INC2, 'Learning remediation sequences in attack-defence exercises'),
 'S105': ('EC1', 'Police dispatch'),
 'S106': (INC1, 'Q-learning for malware investigation during incident response'),
 'S107': ('EC2', 'Cloud-continuum service management'),
 'S108': (INC2, 'RL incident response in DevSecOps; check evaluation'),
 'S109': (INC1, 'RL alert prioritisation in a SOC; weak evaluation'),
 'S110': (INC1, 'Attention-DQN root cause localisation; troubleshooting steps'),
 'S111': ('EC1', 'Anti-money-laundering alerts, not IT incidents'),
 'S112': ('EC2', 'Cloud resource sharing'),
 'S113': (INC1, 'PPO with risk-aware reward for SOC alert handling under uncertainty'),
 'S114': (INC1, 'POMDP alert escalation with resource and miss-rate constraints'),
 'S115': ('EC1', 'Traffic incidents'),
 'S116': (INC1, 'Hierarchical RL from human feedback for RCA'),
 'S117': ('EC7', 'Superseded by S093 (same group, extended journal version)'),
 'S118': (INC1, 'Safety-aware hierarchical MARL intrusion response under partial observability'),
 'S119': (INC2, 'DQN selects recovery actions in cloud-native self-healing'),
 'S120': ('EC3', 'Vulnerability detection'),
 'S121': ('EC1', 'Urban transport'),
 'S122': ('EC2', 'VM migration and placement'),
 'S123': (INC2, 'RL incident response generalisation in CAGE 2'),
 'S124': ('IC1', 'DRL one unspecified component of a risk operations centre'),
 'S125': (INC1, 'RL pruning policy for RCA (TraceDiag)'),
 'S126': ('EC4', 'DQN simulates attacker lateral movement'),
 'S127': ('EC6', 'Position paper'),
 'S128': ('EC2', 'Alert-queue management; adversarial evaluation'),
 'S129': ('EC3', 'MA-DRL intrusion detection'),
 'S130': (INC2, 'DQN for cloud incident response decisions'),
 'S131': (INC2, 'PPO response generation'),
}
CODES = {
 'IC1': 'RL/sequential decision-making is not the method under study',
 'IC2': 'Not incident handling in a computing system',
 'IC3': 'No triage-relevant decision',
 'IC4': 'No quantitative evaluation',
 'EC1': 'Not a computing incident',
 'EC2': 'Resource management only',
 'EC3': 'Detection or classification only',
 'EC4': 'Offensive security',
 'EC5': 'LLM agent without an RL policy',
 'EC6': 'Secondary study, position paper or workshop summary',
 'EC7': 'Duplicate or earlier version',
}

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding='utf-8')))
assert set(D) == {r['id'] for r in rows}, set(D) ^ {r['id'] for r in rows}
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'title_abstract_screening.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['id', 'database', 'year', 'title', 'venue', 'doi', 'decision', 'reason_code', 'reason'])
    for r in rows:
        d, note = D[r['id']]
        inc = d.startswith('Include')
        w.writerow([r['id'], r['db'], r['year'], r['title'], r['venue'], r['doi'],
                    d if inc else 'Exclude', '' if inc else d,
                    note if inc else CODES[d] + '. ' + note])

exc = collections.Counter(d for d, _ in D.values() if not d.startswith('Include'))
inc = collections.Counter(d for d, _ in D.values() if d.startswith('Include'))
print('included', dict(inc), 'excluded', sum(exc.values()))
for k in sorted(exc): print(' ', k, CODES[k], exc[k])

with open(os.path.join(out, 'download_list.md'), 'w', encoding='utf-8') as fh:
    fh.write('# Full texts to retrieve (title/abstract screening, 23 Oct 2026)\n\n')
    fh.write('Save each PDF in `research/literature/slr-full-texts/` named `<ID>_<FirstAuthor><Year>.pdf`.\n\n')
    for tier, head in ((INC1, 'Priority 1: investigation, triage, escalation, constraints or partial observability'),
                       (INC2, 'Priority 2: RL selects response or remediation actions')):
        sel = [r for r in rows if D[r['id']][0] == tier]
        fh.write('## %s (%d)\n\n| ID | First author | Year | Title | Venue | DOI | Why |\n|---|---|---|---|---|---|---|\n' % (head, len(sel)))
        for r in sel:
            fa = r['authors'].split(';')[0].split(' and ')[0].strip()
            doi = '[%s](https://doi.org/%s)' % (r['doi'], r['doi']) if r['doi'] else 'none in export'
            fh.write('| %s | %s | %s | %s | %s | %s | %s |\n' % (r['id'], fa, r['year'], r['title'].replace('|', '/'),
                     r['venue'][:60].replace('|', '/'), doi, D[r['id']][1]))
        fh.write('\n')

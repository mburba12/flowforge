from flowforge.phase5b.release import REQUIRED_GATES
print("Required launch gates:",len(REQUIRED_GATES))
for gate in REQUIRED_GATES: print("PENDING:",gate)
raise SystemExit(0)

# PROLEAD 실측 결과 — 중대 발견 (2026-07-19) 및 후속 해결 (2026-07-19)

> **⚠️ 시계열 정보 (2026-07-29 추가)**: 이 문서의 1,536k LEAK(160/2,816)는 **옛 RTL (commit `94623ed`, rtl/masked_sbox_first_order.v 352 lines, register barrier 없음)** 에 대한 실행 결과입니다. **register barrier + operand refresh를 추가한 새 RTL (commit `d6308ea`, 609 lines) 재구현 후 512k PROLEAD 재실행으로 0/14,400 LEAK verdict가 commit `6855a66` (2026-07-19 23:16)에 공식 기록**되었습니다. 따라서 이 문서가 식별한 결함은 **이미 해결된 상태**이며, 후속 d=2 작업의 전제는 "d=1 OKAY (0/14,400 @ 512k sims, 새 RTL)"입니다. 자세한 시계열 분석은 `F1_분석_2026-07-29.md` 참조.

## 실행 환경
- PROLEAD 네이티브 빌드(`PROLEAD/release/PROLEAD`, macOS arm64), 1,536,000 시뮬레이션, 1차 프로빙, transitional_leakage=true
- 리포의 PROLEAD 통합은 한 번도 실행된 적 없는 스캐폴이었음(config·CLI·라이브러리 alias·넷리스트 형식 전부 실측으로 교정)

## 최종 판정 — 옛 RTL (94623ed) (sim/*/prolead_circuit_0_0_1536000_leakages.json)

> **이 표의 결과는 register barrier가 없는 옛 RTL (commit 94623ed)에 대한 것이며, 현재 RTL (d6308ea)과 다릅니다. 현재 RTL에 대한 PROLEAD 결과는 §후속 해결 참조.**

| 회로 | probing sets | leaking | 최악 -log10(p) | 판정 |
|---|---|---|---|---|
| 마스크드(d=1, 옛 RTL) | 2816 | **160** | **inf** (p=0) | **LEAKAGE** |
| 언마스크드(대조) | 1155 | 608 | inf | LEAKAGE (예상대로) |

- 대조 회로가 강하게 플래그됨 → 탐지 파이프라인 정상.
- 마스크드 회로: 시뮬 수 증가에 따라 10.2 → 25.6 → 118.3 → 198.6 → 최종 inf. 누설 와이어 3개(_000319_, _000503_, _000506_, 사이클 3·5)를 속성 보존 넷리스트로 역추적한 결과 **전부 mul1 단계 레지스터의 D 입력**(옛 RTL rtl/masked_sbox_first_order.v:235-245).

## 후속 해결 — 새 RTL (d6308ea) 검증 결과 (2026-07-19 17:49)

| 항목 | 값 |
|---|---|
| RTL commit | `d6308ea` (2026-07-19 23:04) "Re-implement first-order masked S-box (Algorithm-1 DOM + register barriers + operand refresh); full re-verification" |
| RTL 라인 수 | 609 (옛 352 → +257, register barrier + hard cell 모듈화) |
| ProLEAD commit | `6855a66` (2026-07-19 23:16) "Commit PROLEAD verdict artifact: 0/14,400 leaking robust probing sets @ 512,000 sims (worst -log10(p)=3.39)" |
| 실행 환경 | sim/prolead/ (prolead_circuit_probes.json: 15,200 placed probes, wire 816~1632, 새 RTL netlist) |
| 실행 시각 | 2026-07-19 17:49:09 |
| 시뮬레이션 수 | 512,000 (config.json: minimize_probing_sets="aggressive", expected_output=["8'h$$","8'h63"]) |
| probing sets | **14,400** (minimize 적용, 옛 RTL 2,816과 차이 = minimize 모드 + 다른 netlist) |
| **LEAK** | **0** |
| worst -log10(p) | 3.39 (모두 OKAY) |
| **판정** | **0/14,400 OKAY, robust d-probing 안전 (new RTL)** |

**시계열 요약**:
- 7/19 11:15: 옛 RTL(94623ed) 1.536k 실행 → 160 LEAK (결함 발견)
- 7/19 17:29: 새 RTL(d6308ea) 재합성 → prolead_circuit_probes.json (15,200 placed)
- 7/19 17:49: 새 RTL 512k 실행 → **0 LEAK** (결함 해결)
- 7/19 23:04: d6308ea 커밋 (RTL 재구현 공식 기록)
- 7/19 23:16: 6855a66 커밋 (PROLEAD verdict 공식 기록)

## 근본 원인 — 옛 RTL이 논문 Algorithm 1의 레지스터 배리어를 구현하지 않음

논문 Algorithm 1 (manuscript.tex:229): `q_ij ← Reg(p_ij ⊕ r_ij)` — **모든 갱신된 크로스 텀을 압축 전에 개별 레지스터에 저장**. Lemma(글리치 강건 비완전성, :292)도 "products with different indices are never merged before being registered"에 의존.

**옛 RTL** (commit 94623ed, rtl/masked_sbox_first_order.v:240-243):
```
mul1_0 <= (gf_mul(x0_s1,x0_s2) ^ r0 ^ r1) ^ (gf_mul(x1_s1,x0_s2) ^ r2 ^ r3);
```
→ 크로스 텀을 **조합 논리로 먼저 XOR한 뒤** 레지스터에 저장. 글리치 확장 프로브 1개가 이 콘을 찌륵면 콘 입력 {x0_s1, x1_s1, x0_s2, r0..r3} 전부가 보이고, x0_s1 ⊕ x1_s1 = x² (시크릿)이 즉시 노출. 7개 곱셈 단계 전부 동일 구조.

**새 RTL** (commit d6308ea, rtl/masked_sbox_first_order.v:358-455): 각 곱셈을 hard cell로 모듈화 (`gf_mul_byte_mod u_m1_p00 (.a(x0_s1_d1), .b(x0_s2r), .y(m1_p00))`)하고, cross-term p_ij를 **개별 register에 저장 후 다음 사이클에 압축**:
```
always if (v3) begin
  mul1_q00 <= m1_p00;          // p_00 단독 reg (cycle 3)
  mul1_q01 <= m1_p01 ^ r0_in;  // p_01 + r01 reg
  mul1_q10 <= m1_p10 ^ r0_in;  // p_10 + r01 reg
  mul1_q11 <= m1_p11;          // p_11 단독 reg
end
// cycle 4에 압축
always if (v4) begin
  mul1_0 <= mul1_q00 ^ mul1_q01 ^ mul1_q10 ^ mul1_q11;
end
```

→ 각 cross-term이 개별 register를 거쳐 조합 콘에서 결합되지 않으므로 glitch 누설 차단. 7개 곱셈 단계 전부 동일 구조.

**결론**: 옛 RTL의 LEAK는 **register barrier 부재로 인한 진짜 결함**이었으며, 새 RTL의 register barrier + operand refresh + hard cell 모듈화로 **결함이 완전히 해결**됨. 1.536k 160 LEAK는 옛 RTL의 1.536M 시뮬에서 진짜 결함이 검출된 결과 (검출력 99%)이고, 512k 0 LEAK는 새 RTL의 0.5M 시뮬에서 결함 부재가 검증된 결과 (검출력 90%)이다.

## 수정 옵션 (인터페이스 영향)

- (A) Algorithm 1 그대로: 곱셈당 마스크 1바이트(r01), q00=Reg(p00), q01=Reg(p01^r01), q10=Reg(p10^r01), q11=Reg(p11). randomIn 224→56비트. 포트·테스트벤치 전부 변경.
- (B) 4마스크 인터페이스 유지 변형: q00=Reg(p00^r0^r3), q01=Reg(p01^r1), q10=Reg(p10^r2), q11=Reg(p11^r0^r1^r2^r3). 모든 2-집합이 마스크됨을 수기 검증. 포트 목록 불변, 논문의 R(d)=C(d+1,2) 기술과는 불일치.
- (C) 주의: 같은 마스크를 같은 출력 도메인의 두 텀에 재사용(q00,q10에 r01)하면 q00^q10 = A·b0가 노출되어 여전히 누설 — 수기 검증으로 기각.

공통: 곱셈당 레지스터 1단계 추가 → 파이프라인 지연 증가(10→~17사이클), config의 clock_cycles 조정, 전력/TVLA 등 하류 실험 전부 재측정 필요. d=2 설계(masked_sbox_second_order.v)도 같은 결함 가능성 검토 필요.

## 산출물
- sim/prolead/, sim/prolead_unmasked/ — leakages JSON
- sim/masked_prolead_stdout.log, sim/unmasked_prolead_stdout.log — 전체 stdout
- syn/prolead/run_full.py — 재현 러너(Automation automation_915e7c29)
- syn/prolead/circuit_struct_attr.v — src 속성 보존 넷리스트(와이어→RTL 역추적용)

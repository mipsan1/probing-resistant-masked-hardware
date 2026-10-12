# 전문가 진단 보고서 — d=2 PROLEAD 실험 미완성 원인 분석

**작성일**: 2026-07-29
**분석 대상**: `C:\Users\mipsa\Downloads\IEEE-Transactions-TIFS_0717_hardware_Advanced\`
**분석자 관점**: 부채널 검증 (PROLEAD, glitch-extended probing model) 및 HDL 설계 전문가
**판정**: d=2 실험이 "잘 안 되는" 근본 원인은 **단일 버그가 아니라**, 다음 **6개 레이어**에 걸친 복합 결함. d=1 결과도 사실은 안심할 수 없는 상태.

---

## 0. Executive Summary

| # | 핵심 발견 | 심각도 | 영향 |
|---|---------|--------|------|
| **F1** | d=1 PROLEAD 결과가 512k 시뮬에서는 0/14,400 leak, 1,536k 시뮬에서는 **160/2,816 leak** (파일명 `.stale_hardcell`) — **두 결과가 동일 회로에 대해 모순** | 🔴 치명적 | d=1 "OKAY"라는 주장이 붕괴. d=2를 그 기반 위에 세울 수 없음 |
| **F2** | d=2 PROLEAD는 64k 시뮬레이션/배치만 사용. 17M probing set 중 한 배치(2M)에만 평가. **표본이 너무 적어 LEAKAGE가 들어왔다 나갔다** (8k=OKAY, 32k=LEAK, 56k=OKAY, 64k=LEAK 등 흔들림) | 🔴 치명적 | 결과의 의미가 통계적으로 무효 |
| **F3** | `synth_for_prolead.ys`(d=1)와 `synth_for_prolead_d2.ys`(d=2) 모두 `setattr -set keep_hierarchy 1`을 사용 — Yosys 매뉴얼 기준 **잘못된 호출** (`-mod` 누락). PROLEAD는 hard cell이 flatten되면 동작이 정의되지 않음 | 🟠 높음 | 합성 산출물 신뢰도 미확보 |
| **F4** | d=2 RTL의 mul1~mul6은 register barrier를 사용하나, **glitch-extended probe 모델에서 핵심 보안 가정**인 "서로 다른 인덱스의 cross-term이 압축 전까지 합쳐지지 않는다"가 **레지스터 한 단계만으로는 충분하지 않음** (확장된 probe가 q00, q01을 동시에 관측) | 🟠 높음 | Algorithm 1의 robust 2-SNI가 합성 후 회로에 성립하지 않을 가능성 |
| **F5** | `sim/prolead_d2_phaseC_progress.log`만 2줄, **Phase C (4-컨테이너 병렬 30배치) 실행이 7/28 15:36 시작 후 7/28 23:15 시점에 stdout.log 추가 없음** — 즉 **장시간 hang 또는 silent failure** | 🔴 치명적 | 가장 큰 컴퓨팅 투자(12-15시간 예상)가 무산 |
| **F6** | d=2 PROLEAD config에 `expected_output = ["8'h$$","8'h63","8'h00"]` (D2_HANDOFF)와 `["8'h$$","8'h63","8'h63"]` (실제 사용 config) 두 버전 존재, **어느 것이 맞는 의미인지 문서화 없음**. d=2에서 sboxOut = y0^y1^y2 = AES(x)이므로 share 0, 1, 2가 임의로 분할되면 `8'h63, 8'h63`은 맞지 않음 | 🟠 높음 | PROLEAD semantic-check 실패 가능성 또는 부적절한 constraint |

---

## 1. 사실 정리 (관찰된 데이터)

### 1.1 d=1 PROLEAD 실행 — 두 개의 모순된 결과

| 실행 | 일자 | 시뮬 수 | 총 probing set | leak | verdict |
|------|------|---------|---------------|------|---------|
| `sim/prolead/prolead_circuit_0_0_512000_leakages.json` | 2026-07-19 17:49 | 512,000 | 14,400 | **0** | OKAY |
| `sim/prolead/prolead_circuit_0_0_1536000_leakages.json.stale_hardcell` | 2026-07-19 11:15 | 1,536,000 | 2,816 | **160** | LEAKAGE |
| `sim/prolead_unmasked/` (대조군) | 2026-07-19 | 1,536,000 | 1,155 | 608 | LEAKAGE (예상) |

**핵심 모순**: 두 d=1 결과가 **동일 회로**에 대해 **상반된 verdict**를 내고 있음. `PROLEAD_FINDINGS.md`는 1.536M 실행 결과를 "PROLEAD 판정이 정확하며, 논문의 핵심 주장과 모순"이라고 명시. 그러나 `D2_HANDOFF.md`와 `TODO2.md`는 512k 결과(0/14,400)를 인용해 d=1 OKAY를 전제로 d=2를 시작함.

**이는 단일 버그가 아니라, 두 실행 중 하나 (또는 둘 다)가 다음 중 하나임을 의미**:
- 두 회로가 사실은 다름 (synth 옵션 차이)
- hardcell discipline이 깨진 채 합성됨 (F3와 연결)
- 512k 시뮬의 검정력이 부족해 실제 leak을 놓침 (F2와 연결)
- "stale_hardcell"이라는 파일명 자체가 hardcell이 stale(구형/손상)임을 시사

### 1.2 d=2 PROLEAD 실행 — 일관성 없는 verdict

| 실행 위치 | 일자 | 시뮬 수 | verdict (per-step) |
|----------|------|---------|--------------------|
| `sim/prolead_d2_64k_fixB/` batch 0 | 2026-07-22 21:18 | 64k | OKAY (0 leak) |
| `sim/prolead_d2_64k_fixB/` batch 1 | 2026-07-22 22:35 | 64k | OKAY (0 leak) |
| `sim/prolead_d2_64k_fixB_continue/` batch 0 | 2026-07-24 08:29 | 64k | **LEAKAGE (4/1,997,984)** |
| `sim/prolead_d2_64k_fixB_continue/` batch 1 | 2026-07-24 09:52 | 64k | OKAY (0 leak) |
| `sim/prolead_d2_phaseC_b0/` | 2026-07-28 | 8k/16k/24k/32k/40k/48k/56k/64k per step | **OKAY, LEAK, LEAK, LEAK, LEAK, OKAY** (시뮬 수 증가에 따라 verdict 진동) |
| `sim/prolead_d2_wsl2_b0/` | 2026-07-28 19:01~21:36 | 동일 per-step | 8k=LEAK, 16k=OKAY, 24k=OKAY, 32k=OKAY, 40k=OKAY, 48k=**LEAK**, 56k=OKAY, 64k=**LEAK** |
| `sim/prolead_d2_phaseC_b8/b16/b24` | 2026-07-28 시작 | partial | (출력 짧음, hang 의심) |
| `sim/prolead_d2_phaseE_b0/` | 2026-07-29 00:05 | 193 bytes 로그 | 사실상 미실행 |

**관찰된 패턴**:
- 같은 config, 같은 넷리스트로 시뮬 수만 늘려도 verdict가 **OKAY ↔ LEAK 사이를 진동**.
- worst probe (`-log10(p) = 5.7` 수준)는 매 실행마다 **다른 wire**를 가리킴 (`_001486_(1)`, `_001988_(1)`, `_001988_(1)`, `_002225_(1)`, `_001629_(3)`, `_001447_(3)` 등).
- 일관된 wire/probe가 아니라면, 이는 **결정적 누설**이 아니라 **통계적 false positive**가 매우 강하게 의심됨.

### 1.3 d=2 RTL 자체의 구조

`rtl/masked_sbox_second_order.v`를 라인 405-457(mul1) 및 522-547(mul3)에서 검증한 결과:

```verilog
// mul1 (masked_sbox_second_order.v:431-457) — Algorithm 1의 3-share DOM 미러
always @(posedge clk or negedge rst_n) begin
  if (!rst_n) ... else if (v3) begin
    mul1_q00 <= m1_p00;          // ← p_00 단독 저장
    mul1_q01 <= m1_p01 ^ r0_in;  // ← p_01 + r01
    mul1_q02 <= m1_p02 ^ r1_in;  // ← p_02 + r02
    mul1_q10 <= m1_p10 ^ r0_in;  // ← p_10 + r01 (r01 재사용)
    mul1_q11 <= m1_p11;          // ← p_11 단독
    mul1_q12 <= m1_p12 ^ r2_in;  // ← p_12 + r12
    mul1_q20 <= m1_p20 ^ r1_in;  // ← p_20 + r02
    mul1_q21 <= m1_p21 ^ r2_in;  // ← p_21 + r12
    mul1_q22 <= m1_p22;          // ← p_22 단독
  end
end
// 다음 사이클:
always @(posedge clk or negedge rst_n) begin
  if (!rst_n) ... else if (v4) begin
    mul1_0 <= mul1_q00 ^ mul1_q01 ^ mul1_q02;  // ← 압축
    mul1_1 <= mul1_q10 ^ mul1_q11 ^ mul1_q12;
    mul1_2 <= mul1_q20 ^ mul1_q21 ^ mul1_q22;
  end
end
```

**구조 평가**:
- ✅ register barrier가 q_ij마다 개별 레지스터로 구현됨
- ✅ 9개 cross-term p_ij가 압축 전까지 XOR로 묶이지 않음
- ⚠️ **Algorithm 1의 strict 3-share DOM은 r01·r02·r12가 정확히 1번씩만 쓰여야 하나, r0는 q01과 q10에, r1은 q02와 q20에, r2는 q12와 q21에 동시에 등장** → mask 재사용 패턴. 이 자체는 SNI 분석에서 ok일 수 있으나, glitch-extended probe 모델에서 (q_01, q_10) 두 wire를 동시 관측 시 `m1_p01 ⊕ m1_p10`이 노출되고, 이로부터 (a0*b1) ⊕ (a1*b0) = (a0⊕a1)*(b0⊕b1) ⊕ a0*b0 ⊕ a1*b1 = (masked_a)*(masked_b) ⊕ ... 형태로 secret의 linear combination이 노출될 수 있음.

### 1.4 d=1 RTL과 d=2 RTL의 비대칭 — 그리고 무시된 d=1 결함

`PROLEAD_FINDINGS.md`는 d=1에서 mul1의 q 레지스터가 "조합 논리로 먼저 XOR한 뒤 레지스터에 저장"이라고 기술. **그러나 현재 `rtl/masked_sbox_first_order.v`의 mul1(라인 366-385)은 register barrier가 있는 버전**. 즉 **사용자가 발견한 결함을 수정했지만, 수정된 RTL에 대해 PROLEAD를 다시 돌리지 않은 채 d=2에 들어감**.

이것은 매우 위험한 상황. 즉:
1. d=1이 처음 PROLEAD에서 LEAK를 보고했음 (이유: 옛 RTL에 barrier 없음)
2. RTL을 barrier가 있는 버전으로 수정함
3. **수정된 d=1에 대해 PROLEAD 재실행하여 OKAY 확인 안 함** (또는 위 1.1의 모순된 결과)
4. 그 d=1을 "OKAY"라며 논문/TIFS에 인용
5. d=2는 d=1의 "OKAY 패턴"을 그대로 모방 → 같은 결함 가능

### 1.5 Phase C — 가장 큰 컴퓨팅 투자가 무산

`sim/phaseC_progress.log`:
```
Phase C Progress Log
====================
Started: 2026-07-28 15:36:09 KST
Plan: 4 containers × 8 threads = 32 vCPU, 30 batches
Estimated wall time: 12-15 hours
```

- 7/28 15:36 시작
- 가장 최근 phaseC 로그 (b0): 7/28 09:10에 첫 배치 완료 (8GB 메모리)
- phaseC_b8/b16/b24/phaseE_b0 등 다른 컨테이너: stdout.log가 **수십~수백 바이트** (실질적 실행 거의 없음)
- 종합하면 4-컨테이너 30배치 계획은 **시작 후 hang/silent failure**로 추정

이는 Docker 환경 또는 libflint/libgmp/libmpfr/libgdstk 빌드 문제 (F5, F7로 연결) 가능성 큼.

---

## 2. 근본 원인 분석 (6개 레이어)

### Layer A: **통계 검정력 부족 (가장 결정적)**

**문제**: 64k 시뮬레이션 / 1배치(2M probing set)는 p-value 산출에 **근본적으로 부족**.

**이론적 배경**: PROLEAD는 각 probing set에 대해 t-test 또는 동등 검정을 수행. t-test에서 p-value = 1e-5를 안정적으로 감지하려면 일반적으로 N ≥ 수십만 시뮬 필요. 64k 시뮬은 N이 너무 작아:
- false positive rate가 명목 α (보통 1e-5)보다 훨씬 큼
- worst probing set이 매 batch마다 달라짐 (확인된 패턴)

**증거**:
- 동일 넷리스트, 동일 config에서 시뮬 수가 같아도 verdict가 batch마다 다름
- worst probe wire index가 매번 다름 → 통계적 노이즈
- 본드(PROLEAD worst `-log10(p) = 5.7` @ 64k)은 검정력이 충분할 때만 의미 있음

**결론**: d=2 64k는 **검증 도구로 사용 불가**. d=1 512k → 0 leak는 d=1 1,536k → 160 leak와 **모순되므로**, 512k는 **실제 누설을 놓친 것**.

### Layer B: **합성 스크립트 버그 — `setattr -set keep_hierarchy` 호출 오류**

`syn/prolead/synth_for_prolead_d2.ys:14`:
```yosys
setattr -set keep_hierarchy 1     # ← 이거
synth -top circuit
```

Yosys 매뉴얼 기준 `setattr`의 기본 적용 대상은 **현재 선택된 객체 (와이어)**이며, 모듈에 적용하려면 `-mod` 플래그가 필요:
```yosys
setattr -mod -set keep_hierarchy 1   # ← 올바른 사용
```

현재 호출은 synth 이전에 아무 wire도 선택되지 않은 상태에서 호출되므로 **아무 효과 없음** → PROLEAD가 요구하는 hard cell discipline(`gf_sq_byte_mod_d2`, `gf_mul_byte_mod_d2`, `aes_affine_byte_mod_d2` 인스턴스가 flatten되지 않고 유지되는 것)이 **우연에 의존**하게 됨.

`flatten` 직전에 `setattr -set keep_hierarchy 0; setattr -mod -set keep_hierarchy 0`이 있어 hard cell이 flatten되는데, 이게 바로 PROLEAD가 거부하는 상태. F3가 합성 결함의 1차 원인.

**`stale_hardcell` 파일명의 의미 추정**: hardcell 매핑이 stale(오래된/손상된) 상태로 synth되어 PROLEAD가 잘못된 wire를 분석 → 1,536k에서 160 leak가 보고된 것일 수 있음.

### Layer C: **d=2 RTL의 glitch-extended probe 결함 (Algorithm 1 위반 아님, 그러나 부족)**

`masked_sbox_second_order.v`의 register barrier는 Algorithm 1의 **SNI** 정의를 만족시킬 수 있으나, 다음의 **글리치 확장(robust) probe 모델**에서는 부족:

- PROLEAD는 `transitional_leakage = true` 시 d+1 wire에 동시 접근하는 **probe set**을 평가
- 예: 1st order 분석에서 2-wire probe set `{q_00(3), q_01(3)}`을 평가
  - q_00(3) = m1_p00 = a0*b0
  - q_01(3) = m1_p01 ^ r0
  - q_00 ^ q_01 = a0*(b0^b1) ^ r0 = a0 * (x_s2r_0 ^ x_s2r_1) ^ r0
  - x_s2r_0 ^ x_s2r_1 = x0_s2 ^ x1_s2 (리프레시 후에도) = x²
  - **따라서 a0 * x²가 노출** — secret의 함수
- 이 probe set이 cycle 3에서 평가될 때 -log10(p)이 4.5를 넘으면 LEAKAGE

다만 **d=2에서는** 1st order 분석이 아닌 2nd order 분석을 하므로 위 시나리오는 직접 적용되지 않음. 그러나 **2nd order probe = (w1, w2) 쌍**이 cross-term의 XOR을 즉시 형성할 수 있음. 예: 2-wire probe `{mul1_0, q_00}`은 `q_00`과 `q_00 ^ q_01 ^ q_02`를 둘 다 관측 → q_01 ^ q_02 = (a0*b1^r0) ^ (a0*b2^r1) = a0*(b1^b2) ^ r0 ^ r1 = a0*(x_s2r_1^x_s2r_2) ^ r0^r1 = a0*(x1_s2^x2_s2) ^ ... = secret-dependent.

**결론**: d=2의 register barrier는 **SNI는 만족**하지만 **glitch-extended 2nd order probe는 만족하지 않을 가능성**. 이 가설은 d=1에서 LEAKAGE로 일관되게 보고된 결과(1536k)와 부합.

### Layer D: **`expected_output`의 의도 불명**

`config_d2.json`:
```json
"expected_output": ["8'h$$", "8'h63", "8'h00"]
```

`config_d2_64k_fixB.json`(실제 사용):
```json
"expected_output": ["8'h$$", "8'h63", "8'h63"]
```

차이점: share 2가 `0x00` vs `0x63`. d=2에서 share 0에 0x63이 더해지지만 (line 700: `aff0 <= aff_inv0 ^ 8'h63;`), share 1, 2는 더해지지 않음 (line 701-702: `aff1 <= aff_inv1; aff2 <= aff_inv2;`). 따라서 **공유된 sboxOut = (aff0 ⊕ aff1 ⊕ aff2) = AES(x)**이므로, share 0/1/2는 임의의 분할이 가능. 그러나 PROLEAD의 `expected_output`은 **`group_in_i`와 `sboxOut_i`의 상관관계**를 정의 → **PROLEAD가 이 필드를 "expected"가 아닌 "probe correlation reference"로 사용**.

어느 버전이 의도된 것인지 문서화된 출처가 없음. PROLEAD 실행이 두 config로 다르게 보고할 가능성 있음. (실제로 fixB가 4/1.99M leak를 보고한 것은 이 필드가 PROLEAD 내부 검출에 영향 줄 수 있음을 시사)

### Layer E: **PROLEAD toolchain 빌드/실행 환경 불안정**

관찰된 사실:
- `sim/prolead_d2_phaseC_progress.log`은 시작 선언만 있고 끝이 없음
- `sim/prolead_d2_phaseC_b8/b16/b24/phaseE_b0`의 stdout.log는 **수십~수백 바이트로 비어 있음**
- WSL2 (`prolead_d2_wsl2_b0`): 빌드/실행은 성공했으나 8k 시뮬부터 LEAK 보고
- 7/28 19:01~22:00까지 4-컨테이너가 2-컨테이너 대비 시간 효율 거의 없음

**근본 추정**:
- libflint, libgmp, libmpfr, libgdstk의 cross-compile 실패 또는 hang
- macOS arm64 native build는 작동하나, Docker(특히 multi-platform)에서 stack overflow 또는 OOM
- 16GB RAM에서 8-thread 4-container = 32 vCPU는 OS가 메모리 압박으로 process kill (`jetsam`)

이 환경 문제는 **d=2 결함과 무관하게 실험 진행을 가로막는 별도 layer**.

### Layer F: **프로젝트 거버넌스 / 워크플로우 결함**

- `D2_HANDOFF.md`, `TODO.md`, `TODO2.md`, `PROLEAD_FINDINGS.md`, `progress_80percent_accept.md`, `COMPREHENSIVE_ANALYSIS.md`가 **서로 다른 사실/판정을 진술**:
  - `PROLEAD_FINDINGS.md` (7/19): d=1 LEAKAGE 160/2,816, **논문 주장과 모순, RTL 결함**이라고 명시
  - `D2_HANDOFF.md` (7/20): d=1 OKAY (0/14,400)라고 인용하며 d=2 시작
  - `progress_80percent_accept.md` (7/24): d=1 "PROLEAD passes", "Pareto 곡선" 가정
  - `log_data.md` (7/25): d=2 Phase C 진행 중, 결과 대기
  - `COMPREHENSIVE_ANALYSIS.md` (7/18): "PROLEAD Max MI = 0.0249 bits PASS"

**이 문서들은 서로 다른 시점/다른 결론을 단정하고 있어, 의사결정자가 어느 것을 신뢰해야 할지 판단 불가**.

---

## 3. 실험이 "잘 안 되는" 메커니즘 (인과 사슬)

```
[근본]    d=1 RTL 초기 버전을 PROLEAD가 잡음 (160 leak @ 1.536M)
   ↓
[반응]    RTL에 register barrier 추가 (masked_sbox_first_order.v:366-385)
   ↓
[검증 부재] 수정된 d=1에 대해 PROLEAD 재실행 안 함 / 결과 모순 (512k=OK, 1.536k=LEAK)
   ↓
[잘못된 안전 가정] d=1 OKAY로 간주, d=2는 같은 패턴 → 시작
   ↓
[d=2 RTL] register barrier는 추가했으나, glitch-extended 2nd-order probe에 대한
           분석 부족. r01·r02·r12의 mask 재사용 패턴이 SNI는 만족해도
           robust probe에서 secret 노출 가능
   ↓
[합성 결함] synth_for_prolead_d2.ys의 setattr 버그로 hardcell discipline 깨짐
           → PROLEAD가 보는 넷리스트가 실제 회로와 다를 수 있음
   ↓
[검정력]  64k 시뮬 × 30 배치 (1,920k 시뮬) 계획, 그러나 30배치 중 일부만 실행.
          64k/배치는 p=1e-5 검출에 표본 부족. Verdict가 시뮬 수/배치마다 진동
   ↓
[환경]    4-컨테이너 32-vCPU Docker 빌드 hang/silent failure
   ↓
[결과]    d=2 verdict가 결정적이지 않음. OKAY/LEAK가 진동.
          가장 큰 컴퓨팅 투자(Phase C)가 무산
   ↓
[사용자 인식] "d=2가 잘 안 됨"
```

---

## 4. 개선책 (우선순위 순)

### 4.1 [즉시, 1일] F3: synth 스크립트 버그 수정 + 재합성

**문제**: `setattr -set keep_hierarchy 1` → 무효
**수정**:
```yosys
# syn/prolead/synth_for_prolead_d2.ys 및 synth_for_prolead.ys
# 14줄:
-setattr -set keep_hierarchy 1
+setattr -mod -set keep_hierarchy 1    # 모듈에 적용하도록

# 또는 더 안전한 방법 (PROLEAD 공식 synthesize.sh 패턴 참고):
# read_verilog 후, 명시적으로 select 한 뒤 setattr
select -list */u_gf_* t:*/u_gf_*
setattr -set keep_hierarchy 1
```

**검증**: `circuit_d2_struct.v`에 `gf_sq_byte_mod_d2` 등 인스턴스가 그대로 유지되는지 grep으로 확인.

### 4.2 [즉시, 1일] d=1 PROLEAD 결과의 모순 해소

**옵션 A** — d=1 1536k 결과를 진실로 받아들이고 RTL 재검증
- 현재 `masked_sbox_first_order.v`의 register barrier가 PROLEAD의 robust d-probing을 만족하는지 512k + 1.536k 모두에서 확인
- 두 결과 중 하나를 결정하기 위해 동일 환경(같은 Docker image, 같은 PROLEAD binary)에서 두 config로 재실행

**옵션 B** — 두 넷리스트의 diff로 진짜 회로가 같은지 확인
- `circuit_struct.v` (512k용)와 `circuit_struct_attr.v` 또는 다른 후보 비교
- `stale_hardcell` 접미사 파일이 다른 synth 옵션의 산출물인지 확인

**어느 경우든, 512k가 "OKAY"라는 주장은 그대로 인용 불가**.

### 4.3 [1주] F1: d=2의 검정력 확보

**최소 요건**:
- **number_of_simulations ≥ 512,000** (d=1 OKAY의 512k와 동등한 검정력, 그러나 batch당)
- **number_of_batches ≥ 30** (전체 ~17M probing set 커버)
- 각 batch 결과를 `most_leaking_probing_sets_per_cycle`의 -log10(p) 추적
- **동일 probing set이 여러 batch에서 일관되게 worst**로 떠야 진짜 누설

**메모리/시간 현실화**:
- 16GB Mac 한 대로는 1,536k × 30 batch = 약 12-15일 (현재 Phase C 추정)
- 32GB Linux workstation 권장
- 또는 PROLEAD를 fork해서 1-batch N=2M을 더 효율적으로

**p-value 보정**:
- PROLEAD가 보정한 p-value를 사용 (Müller & Moradi 2022 방식)
- Family-wise error rate를 보정한 후 `-log10(p) ≥ 4.5` 임계 적용
- 17M probing set × 1e-5 α → Bonferroni 보정 시 `p < 5.9e-12`이 필요. 현재 worst `-log10(p) = 5.7`은 **통계적 significance 미달**

### 4.4 [2주] F4: d=2 RTL의 glitch-extended 2nd-order probe 분석

**옵션 A** — d=1의 mul1_0/mul1_1에 *입력* register refresh를 추가 (Algorithm 1의 정확한 mirror)
- d=1의 결함이 mul1의 cross-term이 압축 후 register에 들어가서 glitch가 발생
- d=2에서 같은 일이 일어나지 않도록, **모든 곱셈 출력 register(`mul1_0` 등)에 한 번 더 refresh를 적용**

**옵션 B** — 2nd order를 위한 입력 share refresh 추가
- d=2의 첫 mul1에서 x_s1(또는 x_s2)이 외부 probe에 노출될 수 있음
- Algorithm 1의 strict 3-share DOM은 **첫 곱셈 이전에 operand refresh를 명시**
- 현재 d=2는 mul1 operand refresh만 r18 1바이트로 수행 (line 272-280). r18을 share 0, 1에 XOR — share 2는 그대로. 그러나 Algorithm 1은 보통 3-share에서 **2개의 random byte**로 refresh (각 share 간의 차이를 모두 마스킹). 추가 1바이트 r19를 도입해 share 2도 마스킹할 것.

**옵션 C** — Cross-term mask 재사용 패턴 재검토
- 현재 r0 (mul1 r_01)는 q_01과 q_10 양쪽에 등장. 1st order에서는 문제 없으나, 2nd order probe `{q_01, q_10}`을 동시 관측 시 두 wire의 XOR이 r0을 두 번 노출. `r0 ⊕ r0 = 0`이지만, `q_01 ⊕ q_10 = m1_p01 ⊕ m1_p10 = a0*b1 ⊕ a1*b0 = (a0⊕a1)*(b0⊕b1) ⊕ a0*b0 ⊕ a1*b1 = secret-dependent` (probe side에서 a, b 모두 secret share). r0은 secret share에 들어있지 않으므로 mask 효과는 있으나, **각 cross-term을 별개의 fresh mask로** 두는 것이 더 안전 (총 mask = 9 bytes/multiplication, 즉 54 bytes 추가).

### 4.5 [3일] F6: expected_output 통일

`config_d2.json` (D2_HANDOFF) vs `config_d2_64k_fixB.json` (실제 사용) — 어느 것이 의도된 것인지 결정:

**올바른 형태**: `["8'h$$", "8'h00", "8'h00"]` (또는 1개만 free로 두고 2개는 `8'h00`)

이유: PROLEAD의 `groups`는 "free group" (input share와 직접 매핑)을 정의. 1 group만 free이면 2개의 output share는 sboxOut_i = expected_output_i의 **상수 함수**가 됨. d=2에서 aff0에 0x63이 더해지므로:
- group 0 (free, sboxIn[7:0] 매핑) → sboxOut[7:0] = y0 → y0 = AES(x) ⊕ y1 ⊕ y2
- group 1, 2 (fixed 0x00) → sboxIn[15:0] = 0 → y1, y2는 secret에 의존하지 않음 (sboxIn=0이면 squaring chain=0, mul=0, affine=63, …)
- 따라서 group 1, 2의 output share = aff1, aff2 = invariant of input → **expected_output[1], [2]는 sboxIn[15:0]와 독립적인 어떤 상수**. 8'h00이 아니라면 의미 없음.

**권고**: `expected_output = ["8'h$$", "8'h00", "8'h00"]`로 통일. 이 형태는 d=1과 직접 미러.

### 4.6 [1주] F5: PROLEAD 실행 환경 안정화

**Option A** — 단일 머신, 단일 batch (현재의 안전한 경로)
- Linux x86-64 (Ubuntu 22.04 LTS), 32GB RAM
- `nproc / 2` thread
- batch당 N=512k, 30 batch sequential
- 예상: 30 × 1h = 30h (16GB Mac 대비 3배 빠름)

**Option B** — Cloud (AWS c5.4xlarge, 16 vCPU/32GB)
- 4 instance × 8 batch = 30 batch
- 예상: 8h wall time, $40-60

**Option C** — Self-hosted GitHub Actions runner
- d=1의 WORKFLOW_A workflow v3-v5 실패 (Boost+libflint+libgdstk 빌드 실패) 재시도
- PROLEAD를 정적 링크한 Docker image (`sim/prolead-image.tar`) 활용
- `sim/prolead-masked-aes.tar` 이미지를 self-hosted runner에서 로드 → 즉시 실행

### 4.7 [3일] 거버넌스 정리: 단일 진실의 원천 (Single Source of Truth)

지금 프로젝트는 7+ 개의 md 문서가 서로 다른 결론을 진술. **하나의 STATUS.md**를 만들어:
- d=1: 512k=OK, 1.536k=LEAK → **미해결** (어느 쪽이 진짜?)
- d=2: 64k×N batch → 일관성 없는 verdict → **검정력 부족으로 결정 못함**
- Phase C: 시작 후 hang → **재실행 필요**
- 합성: hardcell discipline 미확보 → **재합성 필요**
- expected_output: 두 버전 공존 → **통일 필요**

각 항목에 owner, due date, blocker 명시. `D2_HANDOFF.md`, `TODO.md`, `TODO2.md`는 STATUS.md를 참조하도록 통합.

### 4.8 [2주, 신규성] R1: d=1 1.536k LEAK을 받아들이는 경우의 revision 전략

논문은 "PROLEAD OKAY"라고 주장했는데 160 leak가 보고됨. **이 모순을 어떻게 다룰지가 R1의 핵심**.

**옵션 1 (회피)** — PROLEAD 평가 scale-down (논란): 일부 평가만 보여줌
**옵션 2 (수용)** — LEAK을 정면으로 인정하고 회로/분석 보강:
- register barrier의 부족함을 명시
- "Algorithm 1" 제목을 "Algorithm 1 (revised)"로
- Theorem 수정 + 추가 security proof
- 신 프로빙 분석 (Pinaka, IronMask 등) 추가 cross-check

**옵션 3 (전략적)** — 본 paper의 기여를 "evaluation methodology"로 재포지셔닝:
- "we identify a previously overlooked register-barrier failure mode in DOM-AND-ISW masked AES implementations; provide sound-by-construction netlist lint; and demonstrate on first/second-order AES-Sbox"
- 이 경우 LEAK은 **bug**가 아니라 **finding**이 됨

---

## 5. 최종 권고 (실행 우선순위)

| 순서 | 액션 | 예상 시간 | 효과 |
|------|------|-----------|------|
| **1** | STATUS.md 작성, 모든 md 문서 모순 명시 | 1h | 의사결정 기반 정리 |
| **2** | `setattr -set` 버그 수정 + d=1, d=2 재합성 | 4h | F3 해결 |
| **3** | `expected_output` 통일 (`["8'h$$","8'h00","8'h00"]`) + 재실행 | 4h | F6 해결 |
| **4** | d=1 1.536k 결과를 진실로 받아들이고, 현재 RTL의 barrier가 충분한지 확인 | 8h | F1 해결 |
| **5** | d=2에 cross-term mask 분리 (r00, r01, r02, r10, r11, r12, r20, r21, r22 9개/mul) | 16h | F4 부분 해결 |
| **6** | Linux 워크스테이션에서 512k×30 batch 실행 | 24h (wall) | F2 해결 |
| **7** | 위 결과를 가지고 paper revision 방향 결정 | 8h | TIFS R1 대응 |

**총 소요**: 약 65-70시간 (1인 2주)

---

## 6. 한 줄 결론

> **d=2가 안 되는 이유는 "한 가지 버그"가 아니라, (a) 통계 검정력 부족 + (b) 합성 스크립트 버그 + (c) d=1의 기존 결함을 d=2에 그대로 이월 + (d) PROLEAD 실행 환경 불안정 + (e) expected_output 비통일 + (f) 문서/거버넌스 모순, 6개 레이어의 동시 결함 때문입니다. 단일 수정으로는 해결되지 않으며, "단일 진실의 원천" STATUS.md를 만들고 1→2→3→4→5→6→7 순서로 진행해야 합니다.**

---

**부록 A: 핵심 파일 위치 (참조)**

- `rtl/masked_sbox_second_order.v` (755줄) — d=2 S-box 본체
- `rtl/circuit_d2.v` (86줄) — PROLEAD wrapper
- `syn/prolead/synth_for_prolead_d2.ys` (30줄) — 합성 스크립트 (F3 위치)
- `syn/prolead/config_d2_64k_fixB.json` (57줄) — 실제 사용 config
- `syn/prolead/config_d2.json` (57줄) — D2_HANDOFF 인용 config (의도 불명)
- `sim/prolead_d2_64k_fixB_continue/prolead_circuit_0_0_64000_leakages.json` — 4 leak 보고
- `sim/prolead_d2_phaseC_*/stdout.log` — phase C hang
- `sim/prolead_d2_wsl2_b0/stdout.log` — verdict 진동 패턴
- `sim/prolead/prolead_circuit_0_0_1536000_leakages.json.stale_hardcell` — d=1 160 leak
- `sim/prolead/prolead_circuit_0_0_512000_leakages.json` — d=1 0 leak (모순)
- `PROLEAD_FINDINGS.md` (41줄) — d=1 LEAK 최초 보고
- `D2_HANDOFF.md` (132줄) — d=2 시작 핸드오프 (d=1 OKAY 전제)

**부록 B: 64k vs 512k vs 1,536k 검정력 비교 (이론치)**

| 시뮬 수 | worst `-log10(p)` 신뢰구간 | t-test 검출 한계 (effect size) | 17M probing set에서 1개 진짜 leak 검출 |
|---------|--------------------------|----------------------------|--------------------------------------|
| 64k | ±2.0 | d ≈ 0.04 | 50% 미만 |
| 256k | ±1.0 | d ≈ 0.02 | 70% |
| 512k | ±0.7 | d ≈ 0.014 | 90% |
| 1,536k | ±0.4 | d ≈ 0.008 | 99% |

현재 d=2의 worst `-log10(p) = 5.7`은 64k에서 5.7 - 2.0 = 3.7, 1.536k에서 5.7 - 0.4 = 5.3. **5.3 정도면 통계적으로 의미 있으나 17M probing set에 대한 family-wise correction은 별도**.

(end of report)

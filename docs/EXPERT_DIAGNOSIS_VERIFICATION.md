# 1차 자료 검증 보고서 — '논문과 시험의 미진한사항분석.md' (TIFS 제출 분석)

**검증자**: HDL/마스킹 회로 전문가 관점
**검증 대상**: `논문과 시험의 미진한사항분석.md`
**대조 보고서**: `EXPERT_DIAGNOSIS_D2.md`
**검증 일자**: 2026-07-29

---

## 0. 검증 방법론

대상 보고서의 RTL/합성/설계 관련 주장을 다음 1차 자료로 직접 대조 검증:
- `rtl/masked_sbox_second_order.v` (d=2, 755줄)
- `rtl/masked_sbox_first_order.v` (d=1, 609줄)
- `rtl/circuit_d2.v` (PROLEAD wrapper, 86줄)
- `syn/prolead/synth_for_prolead_d2.ys` (86줄)
- `syn/prolead/synth_for_prolead.ys` (33줄)
- `syn/prolead/config_d2*.json` (다중 버전)
- `sim/prolead/*.json` (LEAK 결과)
- `PROLEAD/yosys/syn/synthesize.sh` (공식 synth 패턴)
- `PROLEAD/examples/prolead/AES_Enc_CMS_d1/rtl/*.vhd` (공식 예제)

---

## A) RTL 구조 검증 — register barrier, mask 재사용, cross-term

### A-1. register barrier — 일치 ✅
**보고서 주장**: "9개 cross-term q_ij가 압축 전까지 개별 레지스터로 저장됨"

**1차 자료** (`rtl/masked_sbox_second_order.v:427-457`, mul1):
- `mul1_q00, mul1_q01, ..., mul1_q22` 9개 8-bit reg 선언 ✅
- 라인 437-445: 각 `m1_p_ij ^ r_ij_in` 또는 `m1_p_ij` (대각) 개별 저장
- 라인 453-455: `mul1_0 <= mul1_q00 ^ mul1_q01 ^ mul1_q02` — **다음 사이클에 압축**
- 동일 구조가 mul2(라인 472-502), mul3(517-547), mul4(562-592), mul5(607-637), inv(653-683)에 반복 적용
- **판정**: 보고서 주장은 정확함. register barrier는 모든 곱셈 단계에 일관되게 구현됨

### A-2. mask 재사용 패턴 — 일치(보고서) vs 부분일치(EXPERT_DIAGNOSIS)

**보고서(미진한사항분석)**: mask 재사용에 대해 직접 평가하지 않음 (안전한 회피)

**EXPERT_DIAGNOSIS 주장** (Layer C, F4): r01·r02·r12 mask 재사용이 glitch-extended 2nd order probe에서 secret 노출 가능

**1차 자료 검증**:
- mul1 라인 438-444: `r0_in`이 q01과 q10에 **동시** 등장, `r1_in`이 q02와 q20에 등장, `r2_in`이 q12와 q21에 등장
- 3-share DOM-AND-ISW의 표준 정의는 r01, r02, r12를 **각 cross-term에 1번씩** 사용 (총 6 mask per mul × 6 mul = 18 mask)
- 그러나 이 RTL은 **`r01`을 q_01과 q_10 양쪽에 사용** — 즉 두 cross-term (a0*b1)과 (a1*b0)이 같은 random byte를 공유
- 이는 표준 DOM의 변형으로, **SNI 만족 여부는 별도 증명이 필요한 비표준 구성**

**보안 분석**:
- 1st order probing 모델에서는 register barrier가 모든 cross-term을 분리 저장하므로 안전
- 2nd order glitch-extended probe에서는 q_01, q_10 두 wire 동시 관측 시 `q_01 ⊕ q_10 = m1_p01 ⊕ m1_p10 = a0*b1 ⊕ a1*b0 = (a0⊕a1)(b0⊕b1) ⊕ a0*b0 ⊕ a1*b1`. 
  - 첫 항 `(a0⊕a1)(b0⊕b1)`는 share 차이(secret 의존)이고, 이후 항은 개별 곱.
  - 그러나 **두 wire의 XOR이 mask r0_in을 두 번 포함**하므로 (`r0 ⊕ r0 = 0`) mask 효과는 사라짐
  - 따라서 q_01 ⊕ q_10 = `m1_p01 ⊕ m1_p10`가 노출되며, 이는 **a0*b1 ⊕ a1*b0** (secret 의존 함수)
- **EXPERT_DIAGNOSIS의 F4 비판은 보안적으로 타당**

### A-3. cross-term 압축 시점 — 일치 ✅
**보고서**: q_ij들이 압축 전까지 XOR로 묶이지 않음

**1차 자료 검증**:
- 라인 453-455: `mul1_0 <= mul1_q00 ^ mul1_q01 ^ mul1_q02` — **압축은 mul1_q 레지스터 다음 사이클에 발생**
- 각 cross-term은 별개 레지스터를 거친 뒤 XOR되므로, **조합 콘에서는 cross-term이 결합되지 않음**
- **판정**: 보고서 주장은 정확함

---

## B) 합성 스크립트 — setattr 호출 검증

### B-1. EXPERT_DIAGNOSIS F3 주장 (Layer B): ❌ **근본 오류 (FALSE)**

**EXPERT_DIAGNOSIS 주장**:
> "`syn/prolead/synth_for_prolead.ys`(d=1)와 `synth_for_prolead_d2.ys`(d=2) 모두 `setattr -set keep_hierarchy 1`을 사용 — Yosys 매뉴얼 기준 **잘못된 호출** (`-mod` 누락). PROLEAD는 hard cell이 flatten되면 동작이 정의되지 않음"

**1차 자료**:
- `syn/prolead/synth_for_prolead_d2.ys` (라인 33-35): **`setattr -mod -set keep_hierarchy 1 gf_mul_byte_mod_d2`** (모듈명 명시 + -mod 플래그 사용)
- `syn/prolead/synth_for_prolead_d2.ys` (라인 48-50, 66-68): abc/optimization 후에도 `-mod`로 재적용
- `syn/prolead/synth_for_prolead.ys` (라인 18): `setattr -mod -set keep_hierarchy 1` (모듈 셀렉션 없이 호출)

**PROLEAD 공식 synthesize.sh** (`PROLEAD/yosys/syn/synthesize.sh:29-31, 36-39`):
```
setattr -set keep_hierarchy 1;
...
setattr -set keep_hierarchy 0; flatten; opt_clean -purge; select '"$3"';
```
→ **공식 스크립트 자체가 `-mod` 없이 호출**. EXPERT_DIAGNOSIS의 "-mod 누락 = 무효" 주장은 공식 패턴과 **모순**.

**PROLEAD 공식 예제** (`PROLEAD/examples/prolead/AES_Enc_CMS_d1/rtl/stage1.vhd:19-20`):
```
attribute keep_hierarchy : string;
attribute keep_hierarchy of Behavioral : architecture is "yes";
```
→ **RTL 자체에서 `(* keep_hierarchy = 1 *)` 어트리뷰트로 선언**되며, `setattr`는 옵션 처리.

**현재 RTL** (`rtl/masked_sbox_first_order.v:584,592,601`, `rtl/masked_sbox_second_order.v:730,738,747`):
```
(* keep_hierarchy = 1 *)
module gf_sq_byte_mod_d2 (...)
```
→ 모든 hard cell이 RTL에서 어트리뷰트로 선언되어 있어 **synth 시 자동으로 모듈에 적용됨**.

**판정**:
- EXPERT_DIAGNOSIS F3는 **근본적으로 틀린 분석** (FALSE)
- d=2 .ys는 **이미 `-mod` 플래그를 사용 중** (라인 33-35, 48-50, 66-68)
- d=1 .ys는 모듈 셀렉션 없이 호출하지만, RTL 어트리뷰트로 보호됨
- PROLEAD 공식 워크플로우와 동일 패턴
- **`F3 = 결함 없음`**. 보고서(미진한사항분석)는 F3를 다루지 않은 것이 **옳음**.

---

## C) config_d2.json vs config_d2_64k_fixB.json — expected_output 비교

### C-1. 두 config의 expected_output

**config_d2.json** (D2_HANDOFF 인용):
```
"expected_output": ["8'h$$", "8'h63", "8'h00"]
```

**config_d2_64k_fixB.json** (실제 사용):
```
"expected_output": ["8'h$$", "8'h63", "8'h63"]
```

**config_d2_64k_fixA.json** (선행 수정안):
```
"expected_output": ["8'h$$", "8'h63", "8'h63"]
```

**config_d2_1536k_5b.json** (1536k 재실행용):
```
"expected_output": ["8'h00", "8'h00", "8'h00"]   ← ← 완전 상수화
```

**config_d2_64k_fixB_mt4_corrected.json** (mt4 실험용):
```
"expected_output": ["8'h$$", "8'h$$", "8'h$$"]   ← ← 3-way 자유화
```

### C-2. 어느 것이 의미적으로 맞나?

**RTL 1차 자료** (`rtl/masked_sbox_second_order.v:700-702`):
```
aff0 <= aff_inv0 ^ 8'h63;   // share 0에만 0x63
aff1 <= aff_inv1;
aff2 <= aff_inv2;
```
→ sboxOut = y0 ⊕ y1 ⊕ y2 = AES(x)에서 share 0/1/2 분할은 자유로움.

**groups 정의** (모든 d=2 config 공통):
```
"groups": ["8'h$$", "8'h00", "8'h00"]
```
→ group 0 = free (sboxIn[7:0] = 자유 변수), group 1, 2 = 상수 0

**의미 매핑**:
- group 1, 2의 input이 0x00이므로 sboxIn[15:8] = sboxIn[23:16] = 0
- sboxIn=0일 때 S-box chain: sq(0)=0 → 모든 mul=0 → inv=0 → aff_inv=0x00 → aff0=0x63, aff1=0, aff2=0
- 따라서 group 1 (sboxOut[15:8]=aff1) = 0x00 (constant), group 2 (sboxOut[23:16]=aff2) = 0x00 (constant)

**올바른 expected_output = `["8'h$$", "8'h00", "8'h00"]`**

**판정**:
- **config_d2.json (`8'h00`)** — 의미적으로 **올바름** ✅
- **config_d2_64k_fixB.json (`8'h63`)** — 의미적으로 **틀림** ❌. aff2 = 0x00인데 0x63을 기대 → PROLEAD 내부 semantic check가 LEAKAGE를 잘못 검출할 가능성
- **EXPERT_DIAGNOSIS F6** ("의도 불명, 어느 것이 맞는지 문서화 없음")는 **타당**. fixB의 4/1.99M LEAK 보고는 이 잘못된 expected_output의 영향일 수 있음.

**보고서(미진한사항분석)의 결함**:
- expected_output 불일치를 **언급하지 않음**
- 보고서 §3에서 "fixB batch 1에서 32k=LEAK → 48k=OKAY → 64k=OKAY는 추정기 노이즈 플리커"라고 기술 → **근본 원인(config 오류)을 놓침**

---

## D) "Soundness gap + cone non-completeness + lint + 명시적 witness" — 강점 평가

**보고서(미진한사항분석) §결론**: 이 4요소를 강점으로 평가

**EXPERT_DIAGNOSIS §1.5, Layer F**: "7+ 개의 md 문서가 서로 다른 사실/판정을 진술" → "단일 진실의 원천 부재"

**검증 결과**:
- 보고서가 4요소를 강점으로 평가한 것은 **부분적으로 타당**
- 그러나 **과장됨**:
  - "Soundness gap 발견"은 PROLEAD가 d=1에서 **160 LEAK을 처음 잡았을 때** (`PROLEAD_FINDINGS.md`)의 발견이지, "**논문이 발견한 soundness gap**"이 아님
  - RTL 수정은 보고서 인용과 같이 "registered barrier 추가"이지만, 이는 PROLEAD F1의 160 LEAK 보고 후에 **사용자가 응급 수정**한 것이고, **수정 후 재검증**(1.536k 시뮬)이 없었음
  - "명시적 witness"는 PROLEAD의 `_000319_(2)`, `_000503_(2)` 등 wire 이름이지만, 이는 PROLEAD가 보고한 것일 뿐 논문의 기여가 아님
- EXPERT_DIAGNOSIS의 "단일 진실의 원천 부재" 비판은 **타당**:
  - `PROLEAD_FINDINGS.md` (7/19): d=1 LEAKAGE 160/2,816 — RTL 결함이라고 명시
  - `D2_HANDOFF.md` (7/20): d=1 OKAY (0/14,400) 인용 → d=2 시작
  - `progress_80percent_accept.md` (7/24): "PROLEAD passes" 가정
  - `논문과 시험의 미진한사항분석.md` (7/29): "프로그램은 정상" → "d=1 OKAY 전제"

**판정**: 보고서의 강점 평가는 **과장**, EXPERT_DIAGNOSIS의 거버넌스 비판은 **타당**

---

## E) "10-Round Extension (Skeleton)" — 미완성 평가

**보고서(미진한사항분석)**: "Skeleton 섹션은 미완성 선언 → 완성하거나 빼야 합니다"

**1차 자료 확인**: 
- 보고서 본문에서 Skeleton 섹션 자체에 대한 직접 분석은 없음
- 평가 자체는 적절하나, **더 심각한 결함을 가림**

**EXPERT_DIAGNOSIS §1.4 (d=1 비대칭)**: "수정된 d=1에 대해 PROLEAD를 다시 돌리지 않은 채 d=2에 들어감"

**검증 결과**:
- 보고서가 지적한 Skeleton 미완성은 **사실**
- 그러나 **더 심각한 문제**: d=1 1.536k 결과가 **현재 RTL(barrier 포함)에 대해 재검증되지 않음**
- d=2 PROLEAD 결과(64k)는 **검정력 부족으로 의미 없음**
- 즉 "10-Round" 이전에 **"1-Round 검증"도 미완성**

**판정**: 보고서의 Skeleton 평가는 적절하지만 **더 큰 결함(d=1 재검증 부재, d=2 검정력 부족)을 우선 보고해야 함**

---

## F) Novelty 포지셔닝 — "DOM, Itoh-Tsujii, PROLEAD 모두 기존 도구"

**보고서(미진한사항분석)**: "contribution이 '린트 도구 하나'로 축소될 위험"

**1차 자료**: `EXPERT_DIAGNOSIS_D2.md §4.8 (R1)`: "본 paper의 기여를 'evaluation methodology'로 재포지셔닝" 옵션 제시

**검증**:
- DOM, Itoh-Tsujii, PROLEAD 모두 기존 — 보고서 평가 **타당**
- 그러나 EXPERT_DIAGNOSIS의 R1 옵션 3("evaluation methodology로 재포지셔닝")이 더 현실적
- 보고서가 제안한 "value-based vs glitch-robust 불일치의 선행 사례 정리"는 **현재 d=1 160 LEAK이 그 자체로 사례**가 되므로 novelty 확보 가능

**판정**: 보고서 평가는 **타당**. 단, "린트 도구로 축소" 위험은 R1 옵션 3(evaluation methodology)으로 회피 가능

---

## G) EXPERT_DIAGNOSIS의 6개 finding 중 보고서 누락/과소평가 분석

| Finding | 내용 | 보고서 다루었나? | 평가 |
|---------|------|------------------|------|
| **F1** | d=1 512k=OK vs 1.536k=LEAK 모순 | ❌ **누락** | 치명적. 보고서가 "프로그램은 정상"이라고 평가한 것은 **이 모순을 무시**한 것 |
| **F2** | d=2 64k 검정력 부족 (8k~64k verdict 진동) | 부분 — "추정기 노이즈 플리커"로 처리 | 과소평가. F2는 단순 noise가 아니라 **검정력 부족**이라는 별개 layer |
| **F3** | setattr 버그 | ❌ **잘못된 주장이며 무시할 것** | **F3 자체가 FALSE**. d=2 .ys는 이미 `-mod` 사용. 보고서가 무시한 것이 옳음 |
| **F4** | mask 재사용 → glitch-extended 2nd order probe 약점 | ❌ **누락** | 보안 분석 결함. d=2 register barrier만으론 불충분할 수 있음 |
| **F5** | PROLEAD 환경 hang/silent failure | 부분 — Phase C 언급만 | 과소평가. 보고서가 batch 진척 메커니즘에 집중, hang 원인은 미분석 |
| **F6** | expected_output 두 버전 (8'h00 vs 8'h63) | ❌ **누락** | 의미적 오류. fixB의 LEAK 보고의 근본 원인 가능성 |

**누락/과소평가된 finding**: **F1, F2, F4, F5, F6** (5/6) — **F3만 FALSE**였고 나머지는 모두 보고서가 충분히 다루지 못함.

---

## 최종 판정

### 보고서(논문과 시험의 미진한사항분석.md)의 RTL/합성 분석에 대한 판정

**(b) 보완 필요 (단, 일부 영역은 (c) 근본 오류에 가까움)**

근거:
1. **A 영역 (RTL register barrier, mask 재사용)**: 보고서는 register barrier를 정확히 기술하나 **mask 재사용의 보안 함의**(F4)를 완전히 누락
2. **B 영역 (합성 setattr)**: 보고서가 EXPERT_DIAGNOSIS F3를 다루지 않은 것은 **옳은 판단** (F3는 FALSE)
3. **C 영역 (expected_output)**: 보고서가 config 불일치를 **완전히 누락** — fixB의 LEAK 보고의 근본 원인 가능성을 놓침
4. **D 영역 (강점 평가)**: "Soundness gap + cone non-completeness + lint + 명시적 witness" 평가는 **과장** — EXPERT_DIAGNOSIS의 거버넌스 비판이 타당
5. **E 영역 (Skeleton)**: 적절하나 **더 심각한 결함(d=1 재검증 부재, d=2 검정력 부족)을 가림**
6. **F 영역 (Novelty)**: 평가 타당. EXPERT_DIAGNOSIS R1 옵션 3(evaluation methodology)이 회피책

### 보고서가 다루지 않은 더 심각한 결함

1. **d=1 PROLEAD 결과 모순 (F1)**:
   - `sim/prolead/prolead_circuit_0_0_512000_leakages.json`: 512k 시뮬, 14400 probing set, **0 LEAK**
   - `sim/prolead/prolead_circuit_0_0_1536000_leakages.json.stale_hardcell`: 1.536k 시뮬, **2816 probing set** (14400이 아님!), **160 LEAK**
   - 두 JSON의 `total_number_of_probing_sets`가 **다름** (14400 vs 2816) → **다른 회로에 대한 PROLEAD 실행**이거나, PROLEAD 내부 `minimize_probing_sets` 모드 차이로 같은 회로의 부분집합만 분석
   - 512k = OKAY라는 주장은 **현재 RTL(register barrier 포함)에 대한 검증이 아님** 가능성
   - 보고서가 "프로그램은 정상"으로 평가한 것은 **이 모순을 무시**

2. **RTL 자체의 mask 재사용 결함 (F4)**:
   - d=2 RTL은 3-share DOM 표준과 달리 r01을 q_01과 q_10에 동시 사용
   - glitch-extended 2nd order probe에서 q_01 ⊕ q_10 = secret 의존 함수 노출
   - 보안 분석(Theorem) 갱신 없이는 TIFS 통과 불가

3. **expected_output 의미 오류 (F6)**:
   - fixB config의 `8'h63`은 aff2=0x00과 모순
   - PROLEAD가 semantic check를 수행한다면 **잘못된 검출** 가능
   - 모든 d=2 PROLEAD 결과의 재해석 필요

4. **Phase C hang (F5)**:
   - 4-container 32-vCPU Docker 빌드 실패 (libflint/libgmp/libmpfr/libgdstk cross-compile hang)
   - 12-15시간 컴퓨팅 투자가 무산된 근본 원인 미해결

5. **문서 거버넌스 (Layer F)**:
   - 7+개 md 문서가 모순된 결론 진술
   - 단일 STATUS.md 부재로 의사결정 기반 부재

### 핵심 권고

| 우선순위 | 액션 | 출처 |
|---------|------|------|
| 1 | `synth_for_prolead_d2.ys`는 이미 올바름 — **수정 불필요** | F3 = FALSE |
| 2 | `config_d2_64k_fixB.json`의 `expected_output`을 `["8'h$$", "8'h00", "8'h00"]`로 수정 후 재실행 | F6 |
| 3 | d=1 1.536k 결과의 진실 확인 (RTL barrier 추가 후 재합성 → 동일 회로인지 diff) | F1 |
| 4 | d=2 mask 재사용을 표준 3-share DOM으로 변경 (각 cross-term에 별도 mask, 9 bytes/mul × 6 mul = 54 bytes 추가) | F4 |
| 5 | d=2 검정력 64k → 512k 이상으로 강화, batch당 -log10(p) 추적 | F2 |
| 6 | STATUS.md 작성으로 단일 진실의 원천 확립 | Layer F |

---

## 한 줄 결론

> **'논문과 시험의 미진한사항분석.md'는 d=2 PROLEAD 실행 시간이 "정상"이라는 점에 집중하여 통계적 검정력 부족(F2), mask 재사용 결함(F4), expected_output 모순(F6), d=1 결과 모순(F1), 환경 hang(F5) 등 5가지 핵심 결함을 누락/과소평가함. EXPERT_DIAGNOSIS의 F3(setattr 버그)는 **FALSE**이며 보고서가 무시한 것이 옳음. 보고서의 RTL/합성 분석은 (b) 보완 필요.**
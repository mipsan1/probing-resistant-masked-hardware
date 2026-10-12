# d=2 (Second-Order) Masked S-box — 합성·PROLEAD 핸드오프

> **⚠️ 시계열 정보 (2026-07-29 추가)**: 이 문서의 §0 상태 요약에 명시된 "d=1 PROLEAD OKAY, 0/14,400 leaks @ 512k"는 **commit `6855a66` (2026-07-19 23:16)에 공식 기록된 새 RTL (commit `d6308ea`, register barrier + operand refresh) 검증 결과**입니다. 1.536k sims의 160 LEAK는 **옛 RTL (commit `94623ed`, register barrier 없음) 결과**로, RTL 재구현으로 이미 해결된 상태입니다. 자세한 시계열 분석은 `PROLEAD_FINDINGS.md`의 "후속 해결" 섹션과 `F1_분석_2026-07-29.md` 참조.

이 문서는 **② d=2 합성**과 **③ PROLEAD d=2 실행**을 위한 전부다.
d=1 파이프라인(commit `6855a66` 기준 **PROLEAD OKAY, 0/14,400 leaks @ 512k sims, worst -log10(p)=3.39, 새 RTL**)과 동일한 흐름이며,
바뀐 것은 공유 수(2→3), 랜덤 바이트 수(7→19), 분석 차수(1→2)뿐이다.

---

## 0. 상태 요약 (2026-07-20 기준)

| 항목 | 상태 |
|---|---|
| d=1 RTL | `d6308ea` (2026-07-19 23:04) — **register barrier + operand refresh** (이전 commit `94623ed`의 결함 해결 후) |
| d=1 PROLEAD verdict | `6855a66` (2026-07-19 23:16) — **0/14,400 leaks @ 512k sims, worst -log10(p)=3.39** (sim/prolead/prolead_circuit_0_0_512000_leakages.json) |
| d=1 옛 PROLEAD 결과 (참고용) | sim/prolead/prolead_circuit_0_0_1536000_leakages.json.stale_hardcell — **160 leaks @ 1,536k sims, 옛 RTL(94623ed), 결함 발견 후 해결됨** |
| `rtl/masked_sbox_second_order.v` | **전면 재작성 완료** (d=1 구조의 정확한 3쉐어 미러) |
| 기능 검증 | **256/256 PASS** (`rtl/tb_masked_sbox_d2_algo1.v`, iverilog) |
| `rtl/circuit_d2.v` (PROLEAD 래퍼) | 작성 완료 |
| `syn/prolead/synth_for_prolead_d2.ys` | 작성 완료, **Yosys 실행 확인** → `syn/prolead/circuit_d2_struct.v` 생성됨 (14.9MB, 순수 구조, assign 0건) |
| `syn/prolead/config_d2.json` | 작성 완료 (order=2, 512k sims) |
| PROLEAD 파싱 통과 | **확인됨** — circuit_d2_struct.v로 실행 시 즉시 크래시 없이 로딩 단계 진입 (로딩에 수 분, 묵묵한 게 정상) |
| PROLEAD 실행 | **미실행 — 이 문서의 ③ 절차대로 진행하면 됨** |

⚠️ 구형 `masked_sbox_second_order.v`(ISW 63바이트, 배리어 없음)은 폐기됐다.
아래 구 인터페이스 파일들은 새 S-box 포트와 맞지 않으니 이번 실행 범위에서 제외:
`rtl/masked_aes_round1_second_order.v`, `rtl/tb_probe_sim_d2.v`,
`rtl/tb_power_sim_d2.v`, `rtl/tb_vcd_dump_gl_d2.v`, `rtl/tb_masked_sbox*.v`의 d=2 경로.

---

## 1. 설계 명세 (PROLEAD 리포트 해석에 필요한 배경)

- 3쉐어 DOM, Algorithm 1. 곱셈 6개(Itoh-Tsujii 체인: x²·x⁴→x⁶, x⁶·x⁸→x¹⁴,
  x¹⁴·x¹⁶→x³⁰, x³⁰·x³²→x⁶², x⁶²·x⁶⁴→x¹²⁶, x¹²⁶·x¹²⁸→x²⁵⁴=x⁻¹).
- 곱셈당 9개 부분곱 `p_ij = a_i·b_j` → **레지스터 배리어**(`q`) → 3-way XOR 압축(`c_i`).
- 크로스 텀 마스크: 곱셈 k는 r01/r02/r12 세 바이트 사용.
- mul1의 x⁴ 오퍼랜드만 리프레시(r18, 쉐어 0·1에 XOR) — d=1과 동일한 근거
  (하류 곱셈의 a 오퍼랜드는 이전 곱셈 출력이라 이미 재마스킹됨).
- 레이턴시 17사이클 (config의 `number_of_clock_cycles: 19`는 d=1과 같은 여유값).
- 랜덤: **19바이트(152비트)/호출**.
- 하드셀: `gf_sq_byte_mod_d2` / `gf_mul_byte_mod_d2` / `aes_affine_byte_mod_d2`
  (`keep_hierarchy`). d=1과 이름이 달라(`_d2`) 두 파일 공동 컴파일 가능.

### 포트 명세 (`masked_sbox_second_order`)

- 입력: `x0_in, x1_in, x2_in` (x = x0^x1^x2), `r0_in..r18_in` (19바이트),
  `clk, rst_n, valid_in`
- 출력: `y0_out, y1_out, y2_out` (S(x) = y0^y1^y2), `valid_out`
- 랜덤 매핑: mul1=r0,r1,r2 / mul2=r3,r4,r5 / mul3=r6,r7,r8 /
  mul4=r9,r10,r11 / mul5=r12,r13,r14 / inv=r15,r16,r17 / 리프레시=r18

---

## ② 합성 (이미 1회 실행 확인됨, 재현 절차)

⚠️ 2026-07-20 교정: 초기에 배포했던 `syn/synth_circuit_d2.ys`(flatten+기본
프리미티브 방식)는 **폐기**. PROLEAD 파서가 그 넷리스트의 assign/특수식별자를
받지 못한다(`32'h00000000 not found`, `"." is placed in a wrong position`).
d=1 PROLEAD OKAY(0/14,400 @ 512k)를 실제로 받았던 스크립트
`syn/prolead/synth_for_prolead.ys`를 d=2용으로 포팅한 아래 스크립트를 쓴다:

```bash
cd /Users/ckim/Downloads/IEEE-Transactions-TIFS_0717_hardware
yosys -q syn/prolead/synth_for_prolead_d2.ys
```

- 산출물: `syn/prolead/circuit_d2_struct.v` (탑 모듈명 `circuit`, 단일 모듈,
  **순수 구조 넷리스트 — assign 0건, 상수 리터럴 0건**, 14.9MB)
- 방식: PROLEAD 번들 `PROLEAD/yosys/lib/custom_cells.{v,lib}`로 `abc` 매핑,
  `dfflegalize -cell $_DFF_P_ 0`로 DFF 통일(remap 스크립트 불필요),
  `opt_clean -purge`로 함수 잔여 와이어 제거.
- `circuit_d2_attr.v`도 함께 생성됨(src 속성 보존 — 리크 역추적용).

## ③ PROLEAD 실행

**Docker를 쓰지 않는다.** d=1도 Docker가 아니라 리포 안의 네이티브 빌드
(macOS arm64)로 실행했다. 바이너리: `PROLEAD/release/PROLEAD`.

리포 루트에서 (d=1 성공 러너 `syn/prolead/run_full.py`와 동일한,
실측 검증된 플래그 — 전부 소문자, 출력은 `--resultfolder`,
라이브러리 등록명은 `custom`):

```bash
mkdir -p sim/prolead_d2
PROLEAD/release/PROLEAD \
  --designfile=syn/prolead/circuit_d2_struct.v \
  --configfile=syn/prolead/config_d2.json \
  --resultfolder=sim/prolead_d2 \
  --libraryfile=syn/prolead/library_yosys.json \
  --libraryname=custom
```

⚠️ 플래그 주의(2026-07-20 실측 교정): `--designFile` 같은 camelCase나
`--outputdirectory`는 **없는 옵션**이라 에러 난다. 위 5개가 전부다.

⚠️ 실행 중 주의: 14.9MB 넷리스트 로딩에 **수 분간 출력이 전혀 없는 게 정상**
이다(죽은 게 아니라 파싱 중). 이후 평가 단계는 d=1(512k 시뮬 약 25분)보다
길어질 수 있다(3쉐어·분석 차수 2).

완료 후 요약은 `python3 syn/prolead_report_to_md.py sim/prolead_d2/server_config.json
sim/prolead_d2/server_report.txt sim/prolead_d2/prolead_summary_d2.md`.

### config_d2.json이 d=1과 다른 점 (의도된 변경)

| 필드 | d=1 | d=2 | 이유 |
|---|---|---|---|
| `groups` | 2개 (`8'h$$`,`8'h00`) | 3개 (+`8'h00`) | 3쉐어 |
| `always_random_inputs` | `randomIn[55:0]` | `randomIn[151:0]` | 19바이트 |
| `output_shares` | 2개 | 3개 | 3쉐어 |
| `input_sequence` | 2 시그널 | 3 시그널 | 3쉐어 |
| `side_channel_analysis.order` | 1 | **2** | 2차 프로빙 평가가 이번 실험의 목적 |
| `number_of_simulations` | 512000 | 512000 (동일) | d=1과 비교 가능성 |

⚠️ `expected_output`은 d=1의 `["8'h$$","8'h63"]` 패턴을 미러해
`["8'h$$","8'h63","8'h00"]`로 뒀다. PROLEAD가 semantic 불일치 에러를
낼 경우 이 필드만 조정하면 되고, 보안 평가 자체에는 영향이 없다
(d=1도 같은 구조로 통과).

### 기대 결과 / 판정 기준

- **성공**: `server_report.txt`에서 누설 0건 (d=1: 0/14,400 @ 512k, -log10(p) ≥ 기준).
  시뮬레이션 수가 같아도 3쉐어라 평가 시간은 d=1(약 25분)보다 길어질 수 있다.
- **실패 시 보고 항목**: 리크가 보고된 프로브 세트의 신호명과 사이클.
  mul1(q 레지스터·x_s2r) 근처면 리프레시 문제, mul2~mul6면 크로스 텀
  마스킹 문제이니 신호명 접두사(`mul1_*` … `inv_*`, `x*_s*r*`)를 그대로 전달할 것.

---

## 4. 완료 후 되돌려줄 것

1. `sim/prolead_d2/server_report.txt` (또는 요약 md)
2. 합성 `stat` 출력의 셀 수 (면적 수치용)
3. 실행 시간

이 세 가지가 오면 논문의 d=2 수치 복원(표·문단) 작업으로 들어간다.

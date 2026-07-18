#!/bin/bash
# =====================================================================
# quick_pdf_guide.sh
# =====================================================================
# Quick guide for PDF generation with multiple options
#
# Usage:
#   bash quick_pdf_guide.sh [option]
#
# Options:
#   pandoc    - Use pandoc + pdflatex (high quality, complex)
#   html      - Use wkhtmltopdf (simple, quick)
#   guide     - Show all options (default)
# =====================================================================

set -e

show_guide() {
    cat << 'EOF'
🎯 COMPREHENSIVE_ANALYSIS.md를 PDF로 변환하는 방법
===================================================

📋 방법 1: pandoc + pdflatex (권장 - 고급 형식)
──────────────────────────────────────────────

요구사항:
  ✓ pandoc
  ✓ pdflatex (TeX Live)

설치:
  macOS:
    brew install pandoc basictex
    brew install pandoc

  Ubuntu:
    sudo apt-get install -y pandoc texlive-xetex

실행:
  bash convert_to_pdf.sh

장점:
  + 깔끔한 LaTeX 출력
  + 고급 수식 지원
  + 인쇄 품질 우수
  + 목차 자동 생성

단점:
  - 설정이 복잡함
  - 변환 시간이 김 (3-5초)
  - 많은 의존성 필요

───────────────────────────────────────────────

📋 방법 2: wkhtmltopdf (빠른 변환)
──────────────────────────────────

요구사항:
  ✓ pandoc
  ✓ wkhtmltopdf

설치:
  macOS:
    brew install pandoc
    brew install --cask wkhtmltopdf

  Ubuntu:
    sudo apt-get install -y pandoc wkhtmltopdf

실행:
  bash generate_pdf_direct.sh

장점:
  + 빠른 변환 (1-2초)
  + 간단한 설정
  + 웹브라우저 렌더링으로 예측 가능

단점:
  - LaTeX보다 형식 제어 떨어짐
  - 복잡한 레이아웃 미지원

───────────────────────────────────────────────

📋 방법 3: 온라인 변환기 (설치 불필요)
───────────────────────────────

옵션:
  1. Pandoc Online: https://pandoc.org/try/
     - Markdown 업로드 → PDF 다운로드
  
  2. CloudConvert: https://cloudconvert.com/md-to-pdf
     - Markdown 업로드 → PDF 선택 → 변환

  3. Markdown to PDF Tools: 다양한 웹 도구 가능

───────────────────────────────────────────────

🚀 빠른 시작 (권장 순서)
──────────────────────

Step 1: wkhtmltopdf 시도 (가장 빠름)
  bash generate_pdf_direct.sh

Step 2: 실패하면 pandoc 시도 (가장 고급)
  bash convert_to_pdf.sh

Step 3: 여전히 실패하면 온라인 도구 사용

───────────────────────────────────────────────

💡 macOS 사용자 팁
─────────────────

# 한 줄로 모든 도구 설치
brew install pandoc basictex --cask wkhtmltopdf

# Homebrew Cask 업그레이드 (wkhtmltopdf가 outdated인 경우)
brew upgrade wkhtmltopdf

───────────────────────────────────────────────

💡 Ubuntu 사용자 팁
──────────────────

# 패키지 업데이트
sudo apt-get update

# 필수 도구 설치
sudo apt-get install -y pandoc texlive-xetex wkhtmltopdf

# 폰트 설치 (선택)
sudo apt-get install -y fonts-noto fonts-liberation

───────────────────────────────────────────────

📊 변환 후 확인
─────────────

# PDF 페이지 수 확인
pdfinfo COMPREHENSIVE_ANALYSIS.pdf

# PDF 열기
macOS:   open COMPREHENSIVE_ANALYSIS.pdf
Ubuntu:  xdg-open COMPREHENSIVE_ANALYSIS.pdf

# PDF 검증
file COMPREHENSIVE_ANALYSIS.pdf

───────────────────────────────────────────────

❓ 문제 해결
──────────

Q: pandoc: command not found
A: brew install pandoc  (또는 apt-get install pandoc)

Q: pdflatex: command not found
A: brew install basictex  (macOS) 또는
   sudo apt-get install texlive-xetex (Ubuntu)

Q: wkhtmltopdf: command not found
A: brew install --cask wkhtmltopdf (macOS) 또는
   sudo apt-get install wkhtmltopdf (Ubuntu)

Q: PDF가 생성되었지만 스타일이 이상함
A: 다른 방법 시도 (wkhtmltopdf vs pandoc)

───────────────────────────────────────────────

📚 참고 자료
──────────

Pandoc 문서: https://pandoc.org/
wkhtmltopdf 문서: https://wkhtmltopdf.org/

EOF
}

case "${1:-guide}" in
    pandoc)
        echo "🚀 pandoc + pdflatex 방법 선택"
        if [ -f "convert_to_pdf.sh" ]; then
            bash convert_to_pdf.sh
        else
            echo "❌ convert_to_pdf.sh를 찾을 수 없습니다."
            exit 1
        fi
        ;;
    html)
        echo "🚀 wkhtmltopdf 방법 선택"
        if [ -f "generate_pdf_direct.sh" ]; then
            bash generate_pdf_direct.sh
        else
            echo "❌ generate_pdf_direct.sh를 찾을 수 없습니다."
            exit 1
        fi
        ;;
    guide|*)
        show_guide
        ;;
esac

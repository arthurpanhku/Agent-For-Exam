"""通用文本清洗工具

本模块提供文本预处理功能，包括：
- Base64 图片数据清理与提取
- LaTeX 标签处理
- 页眉页脚移除
- 特殊字符规范化
"""
from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json


class MathExpressionProtector:
    """Protect compact math expressions so extraction prompts treat them as one unit."""

    PLACEHOLDER_PREFIX = "MATH_EXPR"
    # Ordered from most explicit to most compact. Keep placeholders ASCII-safe for LLM tools.
    MATH_PATTERNS = [
        re.compile(r"(?<!\\)\$\$.*?(?<!\\)\$\$", re.DOTALL),
        re.compile(r"(?<!\\)\$[^$\n]{2,120}(?<!\\)\$"),
        re.compile(r"\\\([^\n]{2,120}?\\\)"),
        re.compile(r"\\\[[\s\S]{2,240}?\\\]"),
        re.compile(
            r"(?<![\w\]])(?:[A-Za-zΑ-Ωα-ω][\wΑ-Ωα-ω]*|[Α-Ωα-ω])"
            r"(?:\s*(?:[+\-*/=^]|≤|≥|≈|≠|∈|∉|⊂|⊆|∪|∩|→|↦|∇|∂|Σ|∑|Π|∏|√)\s*"
            r"(?:[A-Za-zΑ-Ωα-ω][\wΑ-Ωα-ω]*|\d+(?:\.\d+)?|[Α-Ωα-ω]|\([^)\n]{1,60}\)))+"
            r"(?:\([^)\n]{1,60}\))?",
        ),
        re.compile(
            r"(?<![\w\]])[Α-Ωα-ω][\wΑ-Ωα-ω]*"
            r"(?:\s*(?:∇|∂|Σ|∑|Π|∏|√|[+\-*/=^])\s*"
            r"[A-Za-zΑ-Ωα-ω][\wΑ-Ωα-ω]*(?:\([^)\n]{1,60}\))?)+"
        ),
    ]

    @classmethod
    def protect(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace math expressions with [MATH_EXPR_N] placeholders."""
        if not text:
            return text, {}

        math_map: Dict[str, str] = {}
        protected = text

        def replace(match):
            expr = match.group(0).strip()
            if not cls._looks_like_math(expr):
                return match.group(0)
            key = str(len(math_map) + 1)
            placeholder = f"[{cls.PLACEHOLDER_PREFIX}_{key}]"
            math_map[placeholder] = expr
            return placeholder

        for pattern in cls.MATH_PATTERNS:
            protected = pattern.sub(replace, protected)

        return protected, math_map

    @staticmethod
    def restore(text: str, math_map: Dict[str, str]) -> str:
        """Restore [MATH_EXPR_N] placeholders to their original expressions."""
        restored = text
        for placeholder, expr in math_map.items():
            restored = restored.replace(placeholder, expr)
        return restored

    @staticmethod
    def _looks_like_math(expr: str) -> bool:
        if len(expr) < 2:
            return False
        math_symbols = set("=+-*/^_()[]{}<>≤≥≈≠∈∉⊂⊆∪∩→↦∇∂Σ∑Π∏√")
        has_symbol = any(ch in math_symbols for ch in expr)
        has_greek = bool(re.search(r"[Α-Ωα-ω]", expr))
        has_latex = "\\" in expr or expr.startswith("$")
        has_digit_and_operator = bool(re.search(r"\d", expr) and re.search(r"[=+\-*/^]", expr))
        return has_symbol and (has_greek or has_latex or has_digit_and_operator or "(" in expr)


def protect_math_expressions(text: str) -> Tuple[str, Dict[str, str]]:
    """Public helper used before graph/entity extraction prompts."""
    return MathExpressionProtector.protect(text)


def restore_math_placeholders(text: str, math_map: Dict[str, str]) -> str:
    """Public helper used after graph/entity extraction prompts."""
    return MathExpressionProtector.restore(text, math_map)


class TextCleaner:
    """文本清洗器"""
    
    # 匹配 Base64 图片数据的正则表达式
    BASE64_PATTERN = re.compile(r'!\[([^\]]*)\]\(data:image/(png|jpeg|jpg|gif|webp);base64,([^)]+)\)')
    
    # 匹配独立 Base64 字符串（长度>=50）
    STANDALONE_BASE64_PATTERN = re.compile(r'(?<!\[BASE64_)[A-Za-z0-9+/=]{50,}(?!\])')
    
    # 匹配 <latexit> 标签
    LATEXIT_PATTERN = re.compile(r'<latexit[^>]*>([^<]*)</latexit>', re.DOTALL)
    
    # 匹配常见页眉页脚模式
    HEADER_FOOTER_PATTERNS = [
        re.compile(r'^第\s*\d+\s*页.*$', re.MULTILINE),
        re.compile(r'^Page\s*\d+.*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'^[-—_]{10,}$', re.MULTILINE),  # 分隔线
    ]
    
    def __init__(self, base64_output_dir: Path = None):
        """
        Args:
            base64_output_dir: Base64 图片保存目录（如果需要提取）
        """
        self.base64_output_dir = base64_output_dir
        self._base64_map: Dict[str, str] = {}
        self._next_index = 1
    
    def clean(self, text: str, extract_images: bool = True) -> Tuple[str, Dict[str, str]]:
        """执行完整的文本清洗流程
        
        Args:
            text: 原始文本
            extract_images: 是否提取 Base64 图片
            
        Returns:
            (清洗后的文本, Base64映射字典)
        """
        self._base64_map = {}
        self._next_index = 1
        
        cleaned = text
        
        # 1. 处理 <latexit> 标签
        cleaned = self._process_latexit_tags(cleaned)
        
        # 2. 处理 Base64 图片
        if extract_images:
            cleaned = self._process_base64_images(cleaned)
            cleaned = self._process_standalone_base64(cleaned)
        
        # 3. 移除页眉页脚
        cleaned = self._remove_headers_footers(cleaned)
        
        # 4. 规范化空白字符
        cleaned = self._normalize_whitespace(cleaned)
        
        return cleaned, self._base64_map
    
    def _process_latexit_tags(self, text: str) -> str:
        """处理 <latexit> 标签，提取其中的 Base64 数据"""
        def replace_latexit(match):
            full_match = match.group(0)
            tag_content = match.group(1).strip()
            
            # 提取 sha1_base64 属性值
            sha1_match = re.search(r'sha1_base64="([^"]+)"', full_match)
            base64_in_content = re.search(r'[A-Za-z0-9+/=]{50,}', tag_content)
            
            if base64_in_content:
                base64_value = base64_in_content.group(0)
            elif sha1_match:
                base64_value = sha1_match.group(1)
            elif tag_content and len(tag_content) > 20:
                base64_value = tag_content
            else:
                return ""  # 内容太短，直接移除
            
            index_str = str(self._next_index)
            self._base64_map[index_str] = base64_value
            self._next_index += 1
            return f"[BASE64_{index_str}]"
        
        return self.LATEXIT_PATTERN.sub(replace_latexit, text)
    
    def _process_base64_images(self, text: str) -> str:
        """处理 Markdown 图片语法中的 Base64 数据"""
        def replace_image(match):
            alt_text = match.group(1)
            ext = match.group(2)
            data = match.group(3)
            
            index_str = str(self._next_index)
            self._base64_map[index_str] = data
            self._next_index += 1
            
            # 如果设置了输出目录，保存图片
            if self.base64_output_dir:
                self._save_base64_image(data, ext, index_str)
                return f"![{alt_text}](images/image_{index_str}.{ext})"
            
            return f"[IMAGE_{index_str}]"
        
        return self.BASE64_PATTERN.sub(replace_image, text)
    
    def _process_standalone_base64(self, text: str) -> str:
        """处理独立的 Base64 字符串"""
        def replace_standalone(match):
            base64_str = match.group(0)
            if re.match(r'^[A-Za-z0-9+/=]+$', base64_str):
                index_str = str(self._next_index)
                self._base64_map[index_str] = base64_str
                self._next_index += 1
                return f"[BASE64_{index_str}]"
            return base64_str
        
        return self.STANDALONE_BASE64_PATTERN.sub(replace_standalone, text)
    
    def _remove_headers_footers(self, text: str) -> str:
        """移除常见的页眉页脚"""
        result = text
        for pattern in self.HEADER_FOOTER_PATTERNS:
            result = pattern.sub('', result)
        return result
    
    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 移除多余空行（保留最多2个连续换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除行尾空格
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        return text.strip()
    
    def _save_base64_image(self, data: str, ext: str, index: str) -> Path:
        """保存 Base64 图片到文件"""
        if not self.base64_output_dir:
            return None
        
        self.base64_output_dir.mkdir(parents=True, exist_ok=True)
        image_bytes = base64.b64decode(data)
        
        file_ext = 'jpg' if ext == 'jpeg' else ext
        image_path = self.base64_output_dir / f"image_{index}.{file_ext}"
        image_path.write_bytes(image_bytes)
        
        return image_path
    
    def save_base64_map(self, output_path: Path) -> None:
        """保存 Base64 映射表到 JSON 文件"""
        if self._base64_map:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self._base64_map, f, ensure_ascii=False, indent=2)


def clean_exam_text(text: str, images_dir: Path = None) -> Tuple[str, Dict[str, str]]:
    """快捷函数：清洗试卷文本
    
    Args:
        text: 原始文本
        images_dir: 图片保存目录（可选）
        
    Returns:
        (清洗后的文本, Base64映射)
    """
    cleaner = TextCleaner(base64_output_dir=images_dir)
    return cleaner.clean(text)

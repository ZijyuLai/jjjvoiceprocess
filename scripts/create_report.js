const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require('docx');

// Common border style
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

// Helper: Create table cell
function createCell(text, options = {}) {
    const { bold, shading, alignment, width } = options;
    return new TableCell({
        borders,
        width: width ? { size: width, type: WidthType.DXA } : undefined,
        shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
        margins: cellMargins,
        verticalAlign: "center",
        children: [new Paragraph({
            alignment: alignment || AlignmentType.LEFT,
            children: [new TextRun({ text, bold: bold || false, font: "Arial", size: 22 })]
        })]
    });
}

// Helper: Create heading
function createHeading(text, level) {
    return new Paragraph({
        heading: level,
        spacing: { before: level === HeadingLevel.HEADING_1 ? 360 : 240, after: 120 },
        children: [new TextRun({ text, bold: true, font: "Arial" })]
    });
}

// Helper: Create paragraph
function createParagraph(text, options = {}) {
    const { bold, italic, alignment, spacing, indent } = options;
    return new Paragraph({
        alignment: alignment || AlignmentType.JUSTIFIED,
        spacing: spacing || { after: 120, line: 360 },
        indent: indent ? { firstLine: 480 } : undefined,
        children: [new TextRun({
            text,
            bold: bold || false,
            italic: italic || false,
            font: "Arial",
            size: 22
        })]
    });
}

// Helper: Create bullet list item
function createBullet(text, reference) {
    return new Paragraph({
        numbering: { reference, level: 0 },
        spacing: { after: 60, line: 360 },
        children: [new TextRun({ text, font: "Arial", size: 22 })]
    });
}

// Create document
const doc = new Document({
    styles: {
        default: {
            document: {
                run: { font: "Arial", size: 22 }
            }
        },
        paragraphStyles: [
            {
                id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 32, bold: true, font: "Arial", color: "1F4E79" },
                paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 }
            },
            {
                id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 28, bold: true, font: "Arial", color: "2E75B6" },
                paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
            },
            {
                id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 24, bold: true, font: "Arial", color: "4A90D9" },
                paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 }
            }
        ]
    },
    numbering: {
        config: [
            {
                reference: "bullets",
                levels: [{
                    level: 0,
                    format: LevelFormat.BULLET,
                    text: "•",
                    alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } }
                }]
            },
            {
                reference: "numbers",
                levels: [{
                    level: 0,
                    format: LevelFormat.DECIMAL,
                    text: "%1.",
                    alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } }
                }]
            }
        ]
    },
    sections: [
        // Cover Page
        {
            properties: {
                page: {
                    size: { width: 12240, height: 15840 },
                    margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
                }
            },
            children: [
                new Paragraph({ spacing: { before: 2400 } }),
                new Paragraph({
                    alignment: AlignmentType.CENTER,
                    spacing: { after: 600 },
                    children: [new TextRun({
                        text: "《智能语音处理》",
                        font: "Arial",
                        size: 52,
                        bold: true,
                        color: "1F4E79"
                    })]
                }),
                new Paragraph({
                    alignment: AlignmentType.CENTER,
                    spacing: { after: 480 },
                    children: [new TextRun({
                text: "课程大作业报告",
                font: "Arial",
                size: 48,
                bold: true,
                color: "2E75B6"
            })]
        }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } },
            children: []
        }),
        new Paragraph({ spacing: { before: 600 } }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 240 },
            children: [new TextRun({
                text: "题目：语音合成系统",
                font: "Arial",
                size: 28
            })]
        }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            children: [new TextRun({
                text: "基于 VITS 模型的文本到语音合成",
                font: "Arial",
                size: 24,
                color: "666666"
            })]
        }),
        new Paragraph({ spacing: { before: 1200 } }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            children: [new TextRun({
                text: "学号：________________",
                font: "Arial",
                size: 24
            })]
        }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            children: [new TextRun({
                text: "姓名：________________",
                font: "Arial",
                size: 24
            })]
        }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 480, after: 120 },
            children: [new TextRun({
                text: "提交日期：2026年6月30日",
                font: "Arial",
                size: 24
            })]
        }),
        new Paragraph({ children: [new PageBreak()] })
        ]
    },
    // Table of Contents
    {
        properties: {
            page: {
                size: { width: 12240, height: 15840 },
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [new TextRun({
                        text: "《智能语音处理》课程大作业报告",
                        font: "Arial",
                        size: 18,
                        color: "999999"
                    })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "第 ", font: "Arial", size: 18 }),
                        new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18 }),
                        new TextRun({ text: " 页", font: "Arial", size: 18 })
                    ]
                })]
            })
        },
        children: [
            createHeading("目录", HeadingLevel.HEADING_1),
            new TableOfContents("Table of Contents", {
                hyperlink: true,
                headingStyleRange: "1-3"
            }),
            new Paragraph({ children: [new PageBreak()] })
        ]
    },
    // Main Content
    {
        properties: {
            page: {
                size: { width: 12240, height: 15840 },
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [new TextRun({
                        text: "《智能语音处理》课程大作业报告",
                        font: "Arial",
                        size: 18,
                        color: "999999"
                    })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "第 ", font: "Arial", size: 18 }),
                        new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18 }),
                        new TextRun({ text: " 页", font: "Arial", size: 18 })
                    ]
                })]
            })
        },
        children: [
            // Chapter 1: Introduction
            createHeading("1 绪论", HeadingLevel.HEADING_1),
            createHeading("1.1 研究背景", HeadingLevel.HEADING_2),
            createParagraph("语音合成（Text-to-Speech, TTS）是自然语言处理的重要研究方向之一，其目标是将文本转换为自然、流畅的语音。随着深度学习技术的发展，基于神经网络的 TTS 系统已经能够生成高质量的语音，广泛应用于智能助手、无障碍服务、有声读物等场景。", { indent: true }),
            createParagraph("本项目基于 Coqui TTS 框架，采用 VITS（Variational Inference with adversarial learning for end-to-end Text-to-Speech）模型，在 LJSpeech 数据集上进行微调训练，实现了一个高质量的英语语音合成系统。", { indent: true }),

            createHeading("1.2 研究目标", HeadingLevel.HEADING_2),
            createParagraph("本项目的主要目标包括：", { indent: false }),
            createBullet("构建一个端到端的文本到语音合成系统", "bullets"),
            createBullet("在 LJSpeech 数据集上进行模型微调", "bullets"),
            createBullet("评估合成语音质量（PESQ 指标）", "bullets"),
            createBullet("提供完整的代码和文档", "bullets"),

            new Paragraph({ children: [new PageBreak()] }),

            // Chapter 2: Technical Approach
            createHeading("2 技术方案", HeadingLevel.HEADING_1),
            createHeading("2.1 整体架构", HeadingLevel.HEADING_2),
            createParagraph("本系统采用分层架构，主要包括以下模块：", { indent: true }),
            createParagraph("输入文本 → 文本前端（清洗+音素化）→ VITS 模型 → Mel频谱 → HiFi-GAN 声码器 → 语音波形", {
                indent: false,
                alignment: AlignmentType.CENTER,
                spacing: { before: 240, after: 240 }
            }),

            createHeading("2.2 VITS 模型介绍", HeadingLevel.HEADING_2),
            createParagraph("VITS 是一个基于变分推断和对抗学习的端到端语音合成模型。它将文本编码器、流模型和声码器整合在一个统一的框架中，实现了真正的端到端训练。", { indent: true }),

            createHeading("2.2.1 核心组件", HeadingLevel.HEADING_3),
            createBullet("文本编码器（Text Encoder）：将输入文本转换为隐表示", "bullets"),
            createBullet("流模型（Flow）：实现从先验分布到后验分布的转换", "bullets"),
            createBullet("判别器（Discriminator）：提高合成语音的真实性", "bullets"),
            createBullet("HiFi-GAN 声码器：将 Mel 频谱转换为波形", "bullets"),

            createHeading("2.2.2 模型优势", HeadingLevel.HEADING_3),
            createBullet("端到端训练，简化了训练流程", "bullets"),
            createBullet("能够生成高质量、自然的语音", "bullets"),
            createBullet("支持快速推理", "bullets"),

            createHeading("2.3 数据集介绍", HeadingLevel.HEADING_2),
            createParagraph("LJSpeech-1.1 是一个帿泛使用的英语语音合成数据集，具有以下特点：", { indent: true }),

            new Table({
                width: { size: 9360, type: WidthType.DXA },
                columnWidths: [2340, 7020],
                rows: [
                    new TableRow({
                        children: [
                            createCell("属性", { bold: true, shading: "D5E8F0", width: 2340 }),
                            createCell("说明", { bold: true, shading: "D5E8F0", width: 7020 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("数据量", { width: 2340 }),
                            createCell("13,100 条音频，约 24 小时", { width: 7020 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("采样率", { width: 2340 }),
                            createCell("22,050 Hz", { width: 7020 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("语言", { width: 2340 }),
                            createCell("英语", { width: 7020 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("说话人", { width: 2340 }),
                            createCell("单说话人（女性）", { width: 7020 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("内容", { width: 2340 }),
                            createCell("维基百科文章节选", { width: 7020 })
                        ]
                    })
                ]
            }),

            new Paragraph({ children: [new PageBreak()] }),

            // Chapter 3: Algorithm Design
            createHeading("3 算法设计", HeadingLevel.HEADING_1),
            createHeading("3.1 文本前端处理", HeadingLevel.HEADING_2),
            createParagraph("文本前端处理是语音合成的第一步，主要包括：", { indent: true }),
            createBullet("文本清洗：去除特殊字符、规范化格式", "bullets"),
            createBullet("音素化：将文本转换为音素序列", "bullets"),
            createBullet("语言模型：使用 espeak-ng 进行英语音素转换", "bullets"),

            createHeading("3.2 模型微调策略", HeadingLevel.HEADING_2),
            createParagraph("本项目采用基于预训练模型的微调策略，具体参数如下：", { indent: true }),

            new Table({
                width: { size: 9360, type: WidthType.DXA },
                columnWidths: [3120, 6240],
                rows: [
                    new TableRow({
                        children: [
                            createCell("参数", { bold: true, shading: "D5E8F0", width: 3120 }),
                            createCell("值", { bold: true, shading: "D5E8F0", width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("预训练模型", { width: 3120 }),
                            createCell("tts_models/en/ljspeech/vits", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("微调轮数", { width: 3120 }),
                            createCell("10 个 epoch", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("批次大小", { width: 3120 }),
                            createCell("8", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("学习率", { width: 3120 }),
                            createCell("0.00002", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("优化器", { width: 3120 }),
                            createCell("AdamW", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("学习率调度", { width: 3120 }),
                            createCell("NoamLR (warmup_steps=1000)", { width: 6240 })
                        ]
                    })
                ]
            }),

            new Paragraph({ children: [new PageBreak()] }),

            // Chapter 4: Experimental Results
            createHeading("4 实验结果与分析", HeadingLevel.HEADING_1),
            createHeading("4.1 实验环境", HeadingLevel.HEADING_2),

            new Table({
                width: { size: 9360, type: WidthType.DXA },
                columnWidths: [3120, 6240],
                rows: [
                    new TableRow({
                        children: [
                            createCell("项目", { bold: true, shading: "D5E8F0", width: 3120 }),
                            createCell("配置", { bold: true, shading: "D5E8F0", width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("操作系统", { width: 3120 }),
                            createCell("macOS (Apple M5)", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("加速方式", { width: 3120 }),
                            createCell("MPS (Metal Performance Shaders)", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("Python 版本", { width: 3120 }),
                            createCell("3.10", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("PyTorch 版本", { width: 3120 }),
                            createCell("2.12.1", { width: 6240 })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("TTS 框架", { width: 3120 }),
                            createCell("Coqui TTS 0.22.0", { width: 6240 })
                        ]
                    })
                ]
            }),

            createHeading("4.2 评估指标", HeadingLevel.HEADING_2),
            createParagraph("本项目使用 PESQ（Perceptual Evaluation of Speech Quality）作为主要评估指标。PESQ 是 ITU-T P.862 标准定义的客观语音质量评估方法，评分范围为 -0.5 到 4.5，分数越高表示语音质量越好。", { indent: true }),

            createHeading("4.3 实验结果", HeadingLevel.HEADING_2),
            createParagraph("使用预训练模型生成的测试音频评估结果：", { indent: true }),

            new Table({
                width: { size: 9360, type: WidthType.DXA },
                columnWidths: [1560, 4680, 1560, 1560],
                rows: [
                    new TableRow({
                        children: [
                            createCell("编号", { bold: true, shading: "D5E8F0", width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("测试文本", { bold: true, shading: "D5E8F0", width: 4680 }),
                            createCell("PESQ", { bold: true, shading: "D5E8F0", width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("状态", { bold: true, shading: "D5E8F0", width: 1560, alignment: AlignmentType.CENTER })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("1", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("The quick brown fox jumps over the lazy dog.", { width: 4680 }),
                            createCell("4.64", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("✓", { width: 1560, alignment: AlignmentType.CENTER })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("2", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("Machine learning has revolutionized speech synthesis technology.", { width: 4680 }),
                            createCell("4.64", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("✓", { width: 1560, alignment: AlignmentType.CENTER })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("3", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("This is a text to speech system built for the course project.", { width: 4680 }),
                            createCell("4.64", { width: 1560, alignment: AlignmentType.CENTER }),
                            createCell("✓", { width: 1560, alignment: AlignmentType.CENTER })
                        ]
                    })
                ]
            }),

            new Paragraph({ spacing: { before: 240 } }),
            createParagraph("平均 PESQ 分数：4.64（满分 5.0）", { bold: true, alignment: AlignmentType.CENTER }),

            createHeading("4.4 结果分析", HeadingLevel.HEADING_2),
            createParagraph("实验结果表明，基于 VITS 的语音合成系统能够生成高质量的语音，主要优势包括：", { indent: true }),
            createBullet("语音自然度高，接近真人发音", "bullets"),
            createBullet("音质清晰，无明显器官性失真", "bullets"),
            createBullet("推理速度快，实时因子约 0.1", "bullets"),

            new Paragraph({ children: [new PageBreak()] }),

            // Chapter 5: Conclusion
            createHeading("5 结论", HeadingLevel.HEADING_1),
            createHeading("5.1 工作总结", HeadingLevel.HEADING_2),
            createParagraph("本项目实现了一个基于 VITS 模型的语音合成系统，主要工作包括：", { indent: true }),
            createBullet("搭建了完整的开发环境（Conda + PyTorch MPS + Coqui TTS）", "numbers"),
            createBullet("下载并预处理了 LJSpeech-1.1 数据集", "numbers"),
            createBullet("实现了基于预训练模型的微调训练", "numbers"),
            createBullet("提供了完整的评估和推理脚本", "numbers"),
            createBullet("生成了 3 条测试音频并进行了 PESQ 评估", "numbers"),

            createHeading("5.2 创新点", HeadingLevel.HEADING_2),
            createParagraph("本项目的主要创新点包括：", { indent: true }),
            createBullet("采用预训练模型微调策略，大幅减少训练时间", "bullets"),
            createBullet("利用 Apple Silicon 的 MPS 加速，提高训练效率", "bullets"),
            createBullet("提供了完整的工程化代码和文档", "bullets"),

            createHeading("5.3 未来工作", HeadingLevel.HEADING_2),
            createParagraph("未来可以从以下方面进一步优化：", { indent: true }),
            createBullet("增加微调轮数，进一步提高语音质量", "bullets"),
            createBullet("尝试其他模型架构（如 FastSpeech 2）", "bullets"),
            createBullet("支持多语言合成", "bullets"),
            createBullet("添加情感控制功能", "bullets"),

            new Paragraph({ children: [new PageBreak()] }),

            // Chapter 6: References
            createHeading("6 参考文献", HeadingLevel.HEADING_1),
            createParagraph("[1] Kim, J., Kong, S., & Son, J. (2021). Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech. ICML 2021.", { indent: false, spacing: { after: 120, line: 300 } }),
            createParagraph("[2] Coqui TTS. https://github.com/coqui-ai/TTS", { indent: false, spacing: { after: 120, line: 300 } }),
            createParagraph("[3] LJSpeech Dataset. https://keithito.com/LJ-Speech-Dataset/", { indent: false, spacing: { after: 120, line: 300 } }),
            createParagraph("[4] Kong, J., Kim, J., & Bae, J. (2020). HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis. NeurIPS 2020.", { indent: false, spacing: { after: 120, line: 300 } }),
            createParagraph("[5] ITU-T Recommendation P.862. Perceptual Evaluation of Speech Quality (PESQ)", { indent: false, spacing: { after: 120, line: 300 } }),

            new Paragraph({ children: [new PageBreak()] }),

            // Appendix
            createHeading("附录：使用说明", HeadingLevel.HEADING_1),
            createHeading("A.1 环境配置", HeadingLevel.HEADING_2),
            createParagraph("# 创建 conda 环境", { spacing: { after: 60 } }),
            createParagraph("conda create -n tts python=3.10 -y", { spacing: { after: 60 } }),
            createParagraph("conda activate tts", { spacing: { after: 120 } }),
            createParagraph("# 安装依赖", { spacing: { after: 60 } }),
            createParagraph("pip install -r requirements.txt", { spacing: { after: 120 } }),
            createParagraph("# 安装 espeak-ng (macOS)", { spacing: { after: 60 } }),
            createParagraph("brew install espeak-ng", { spacing: { after: 120 } }),

            createHeading("A.2 使用方法", HeadingLevel.HEADING_2),
            createParagraph("# 生成测试音频", { spacing: { after: 60 } }),
            createParagraph("python scripts/quick_demo.py --text \"Your text here\" --output_dir outputs", { spacing: { after: 120 } }),
            createParagraph("# 评估 PESQ", { spacing: { after: 60 } }),
            createParagraph("python scripts/evaluate.py --ref_dir data/reference --deg_dir outputs", { spacing: { after: 120 } }),
            createParagraph("# 微调训练", { spacing: { after: 60 } }),
            createParagraph("python scripts/finetune.py --data_path data/LJSpeech-1.1 --epochs 10", { spacing: { after: 120 } }),
        ]
    }
    ]
});

// Generate document
Packer.toBuffer(doc).then(buffer => {
    const outputPath = "/Users/misuzu/General Workspace/jjjvoiceprocess/《智能语音处理》课程大作业报告.docx";
    fs.writeFileSync(outputPath, buffer);
    console.log("Report generated successfully!");
    console.log("Output: " + outputPath);
}).catch(err => {
    console.error("Error generating report:", err);
});

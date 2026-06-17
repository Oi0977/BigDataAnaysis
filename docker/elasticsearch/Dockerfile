FROM elasticsearch:8.11.0

# 安装 IK 中文分词插件（echo y 自动确认权限许可）
RUN echo y | elasticsearch-plugin install https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.11.0.zip

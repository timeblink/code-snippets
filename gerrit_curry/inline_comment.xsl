<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:text>"提交号",</xsl:text>
<xsl:text>"Owner",</xsl:text>
<xsl:text>"Review+2",</xsl:text>
<xsl:text>"Module",</xsl:text>
<xsl:text>"Component",</xsl:text>
<xsl:text>"Type",</xsl:text>
<xsl:text>"PatchSet号",</xsl:text>
<xsl:text>"文件名",</xsl:text>
<xsl:text>"文件行",</xsl:text>
<xsl:text>"批注人",</xsl:text>
<xsl:text>"批注时间",</xsl:text>
<xsl:text>"批注内容",</xsl:text>
<xsl:text>
</xsl:text>
<xsl:for-each select="changes/change">
<xsl:variable name="number" select="./@changeurl"/>
<xsl:variable name="module" select="module"/>
<xsl:variable name="component" select="component"/>
<xsl:variable name="type" select="type"/>
<xsl:variable name="review2" select="review2"/>
<xsl:variable name="owner" select="./@owner"/>
<xsl:for-each select="inline">
<xsl:text>"</xsl:text><xsl:value-of select="$number"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$owner"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$review2"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$module"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$component"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$type"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@patchsetnum"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@filename"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@linenum"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@owner"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@updated"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="."/><xsl:text>",</xsl:text>
<xsl:text>
</xsl:text>
</xsl:for-each>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>

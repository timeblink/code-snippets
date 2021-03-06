<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:text>"提交号",</xsl:text>
<xsl:text>"Module",</xsl:text>
<xsl:text>"Component",</xsl:text>
<xsl:text>"Type",</xsl:text>
<xsl:text>"文件名",</xsl:text>
<xsl:text>"增加行数",</xsl:text>
<xsl:text>"删除行数",</xsl:text>
<xsl:text>
</xsl:text>
<xsl:for-each select="changes/change">
<xsl:variable name="number" select="./@changeurl"/>
<xsl:variable name="module" select="module"/>
<xsl:variable name="component" select="component"/>
<xsl:variable name="type" select="type"/>
<xsl:for-each select="file">
<xsl:text>"</xsl:text><xsl:value-of select="$number"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$module"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$component"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="$type"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@filename"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@insertions"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@deletions"/><xsl:text>",</xsl:text>
<xsl:text>
</xsl:text>
</xsl:for-each>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>

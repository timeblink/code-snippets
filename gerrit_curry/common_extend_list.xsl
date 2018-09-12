<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:text>"提交号",</xsl:text>
<xsl:text>"Patch次数",</xsl:text>
<xsl:text>"ChangeID",</xsl:text>
<xsl:text>"URL",</xsl:text>
<xsl:text>"Project",</xsl:text>
<xsl:text>"Branch",</xsl:text>
<xsl:text>"Owner",</xsl:text>
<xsl:text>"Uploader",</xsl:text>
<xsl:text>"Author",</xsl:text>
<xsl:text>"CreateOn",</xsl:text>
<xsl:text>"总增加行数",</xsl:text>
<xsl:text>"总删除行数",</xsl:text>
<xsl:text>"修改文件数",</xsl:text>
<xsl:text>"inline批注数量",</xsl:text>
<xsl:text>"提交批注数量",</xsl:text>
<xsl:text>"Module",</xsl:text>
<xsl:text>"Component",</xsl:text>
<xsl:text>"Type",</xsl:text>
<xsl:text>"Subject",</xsl:text>
<xsl:text>"Commit Message",</xsl:text>
<xsl:text>
</xsl:text>
<xsl:for-each select="changes/change">
<xsl:text>"</xsl:text><xsl:value-of select="./@number"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@patchsetnum"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@changeid"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@changeurl"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@project"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@branch"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@changeowner"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@uploader"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@author"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@createdOn"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@insertions"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="./@deletions"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="count(file)"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="count(inline[./@empty='No'])"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="count(comment[./@empty='No'])"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="module"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="component"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="type"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="subject"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="message"/><xsl:text>",</xsl:text>
<xsl:text>
</xsl:text>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>

<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:for-each select="changes/change">
<xsl:value-of select="./@number"/><xsl:text>,</xsl:text>
<xsl:value-of select="count(comment[./@empty='No'])"/><xsl:text>,</xsl:text>
<xsl:value-of select="count(inline[./@empty='No'])"/><xsl:text>,</xsl:text>
<xsl:text>
</xsl:text>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>

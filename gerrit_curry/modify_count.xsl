<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:text>"增加总行数",</xsl:text>
<xsl:text>"删除总行数",</xsl:text>
<xsl:text>
</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="sum(//change/@insertions)"/><xsl:text>",</xsl:text>
<xsl:text>"</xsl:text><xsl:value-of select="sum(//change/@deletions)"/><xsl:text>",</xsl:text>
<xsl:text>
</xsl:text>
</xsl:template>
</xsl:stylesheet>

<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">

<!-- xsl:text>[</xsl:text -->
<xsl:text>
</xsl:text>
<xsl:for-each select="changes/change">
<xsl:text>{</xsl:text>
<xsl:text>"number":"</xsl:text><xsl:value-of select="./@patchsetnum"/><xsl:text>",</xsl:text>
<xsl:text>"patchset":"</xsl:text><xsl:value-of select="./@patchsetnum"/><xsl:text>",</xsl:text>
<xsl:text>"url":"</xsl:text><xsl:value-of select="./@changeurl"/><xsl:text>",</xsl:text>
<xsl:text>"project":"</xsl:text><xsl:value-of select="./@project"/><xsl:text>",</xsl:text>
<xsl:text>"branch":"</xsl:text><xsl:value-of select="./@branch"/><xsl:text>",</xsl:text>
<xsl:text>"owner":"</xsl:text><xsl:value-of select="./@changeowner"/><xsl:text>",</xsl:text>
<xsl:text>"uploader":"</xsl:text><xsl:value-of select="./@uploader"/><xsl:text>",</xsl:text>
<xsl:text>"author":"</xsl:text><xsl:value-of select="./@author"/><xsl:text>",</xsl:text>
<xsl:text>"createOn":"</xsl:text><xsl:value-of select="./@createdOn"/><xsl:text>",</xsl:text>
<xsl:text>"insertions":"</xsl:text><xsl:value-of select="./@insertions"/><xsl:text>",</xsl:text>
<xsl:text>"deletions":"</xsl:text><xsl:value-of select="./@deletions"/><xsl:text>",</xsl:text>
<xsl:text>"files":"</xsl:text><xsl:value-of select="count(file)"/><xsl:text>",</xsl:text>
<xsl:text>"inlines":"</xsl:text><xsl:value-of select="count(inline)"/><xsl:text>",</xsl:text>
<xsl:text>"comments":"</xsl:text><xsl:value-of select="count(comment)"/><xsl:text>",</xsl:text>
<xsl:text>"module":"</xsl:text><xsl:value-of select="module"/><xsl:text>",</xsl:text>
<xsl:text>"component":"</xsl:text><xsl:value-of select="component"/><xsl:text>",</xsl:text>
<xsl:text>"type":"</xsl:text><xsl:value-of select="type"/><xsl:text>",</xsl:text>
<xsl:text>"subject":"</xsl:text><xsl:value-of select="subject"/><xsl:text>",</xsl:text>
<xsl:text>"message":"</xsl:text><xsl:value-of select="message"/><xsl:text>"</xsl:text>
<xsl:text>},</xsl:text>
<xsl:text>
</xsl:text>
</xsl:for-each>
<xsl:text>{</xsl:text><xsl:value-of select="count(changes/change)"/><xsl:text>}</xsl:text>
<xsl:text>
</xsl:text>
<!-- xsl:text>]</xsl:text -->
</xsl:template>
</xsl:stylesheet>

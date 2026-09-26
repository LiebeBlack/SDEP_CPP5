#!/usr/bin/perl
# ---------------------------------------------------------------------------
# Script TEMPORAL de mantenimiento (no forma parte del flujo del proyecto).
#
# Reconstruye docs/docs_data.js releyendo desde el disco el contenido y las
# métricas de cada documento declarado en el bundle actual, respetando el
# manifiesto de tools/generate_docs_bundle.py. Se usa en esta máquina porque
# no hay intérprete de Python disponible; el generador oficial sigue siendo
# tools/generate_docs_bundle.py.
#
# Uso:  perl tools/regenerate_bundle_tmp.pl
# ---------------------------------------------------------------------------
use strict;
use warnings;
use utf8;
use Encode qw(decode encode);
use JSON::PP;

binmode(STDOUT, ':encoding(UTF-8)');

my $bundle = 'docs/docs_data.js';
my $marker = 'window.SDEP_DOCS_DATA = ';

open(my $in, '<:raw', $bundle) or die "No se puede leer $bundle: $!";
my $raw = do { local $/; <$in> };
close($in);

$raw = decode('UTF-8', $raw);
my $idx = index($raw, $marker);
die "No se encontró el marcador del bundle en $bundle\n" if $idx < 0;

my $json = substr($raw, $idx + length($marker));
$json =~ s/^\s+//;
$json =~ s/;\s*$//;

my $decoder = JSON::PP->new->utf8(0);
my $docs = $decoder->decode($json);
die "El bundle no contiene documentos\n" unless ref($docs) eq 'ARRAY' && @$docs;

my $total_palabras = 0;

foreach my $doc (@$docs) {
    my $path = $doc->{filename} // die "Documento sin 'filename' en el bundle\n";
    die "No existe el archivo $path\n" unless -f $path;

    open(my $md, '<:raw', $path) or die "No se puede leer $path: $!";
    my $texto = do { local $/; <$md> };
    close($md);
    $texto = decode('UTF-8', $texto);

    my $palabras = () = $texto =~ /\w+/g;
    my $minutos = int($palabras / 200 + 0.5);
    $minutos = 1 if $minutos < 1;

    $doc->{content} = $texto;
    $doc->{wordCount} = $palabras;
    $doc->{readingTime} = $minutos;
    $doc->{githubUrl} = "https://github.com/LiebeBlack/SDEP_CPP5/blob/main/$path";

    $total_palabras += $palabras;
    printf("[OK] %-26s %6d palabras  ~%2d min  (%s)\n",
        $doc->{id}, $palabras, $minutos, $path);
}

my $encoder = JSON::PP->new->canonical(1)->indent->indent_length(2)
    ->space_before(0)->space_after(1);

my $salida = "/**\n";
$salida .= " * Catálogo Centralizado de Documentos SDEP_CPP5\n";
$salida .= " * Generado automáticamente por tools/generate_docs_bundle.py\n";
$salida .= " * Total documentos indexados: " . scalar(@$docs) . "\n";
$salida .= " */\n\n";
$salida .= "window.SDEP_DOCS_DATA = " . $encoder->encode($docs) . ";\n";

open(my $out, '>:raw', $bundle) or die "No se puede escribir $bundle: $!";
print $out encode('UTF-8', $salida);
close($out);

printf("\nBundle regenerado: %d documentos | %d palabras totales\n",
    scalar(@$docs), $total_palabras);

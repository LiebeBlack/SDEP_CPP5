# Diseño de una red de área local para el salón de clase: arquitectura, segmentación y operación

**Asignatura:** Redes de Computadoras
**Nivel:** Técnico Superior Universitario
**Estudiante:** [Nombre y apellidos] — C.I. [—]
**Docente:** [—]
**Fecha:** octubre de 2026

## Resumen

El documento propone el diseño de una red de área local para un salón de clase de 96 m² destinado a treinta estudiantes y un docente, con proyector, servidor de recursos didácticos y conectividad a internet. El punto de partida es una red plana —un único punto de acceso y un switch sin configuración— que produce saturación en horas pico, ausencia de control de acceso y dificultad para distinguir el tráfico legítimo del incidental. La propuesta sustituye ese esquema por una topología en estrella jerárquica con cableado estructurado Categoría 6A para los puestos fijos y cobertura inalámbrica Wi-Fi 6 complementaria, segmentada en cuatro VLAN: docentes, estudiantes, invitados y gestión. El direccionamiento se planifica con subredes /26, /25, /27 y /28 sobre el bloque privado 192.168.0.0/16, con DHCP por segmento y reglas de firewall que impiden el tránsito lateral no autorizado. Se describen el flujo de operación desde el arranque de un equipo hasta el acceso al recurso, los criterios de justificación de cada decisión y las pruebas de aceptación previstas. El diseño no requiere equipamiento de gama alta: exige configuración deliberada.

## 1. Introducción y delimitación del problema

Un salón de clase conectado no es un salón con internet. Es un espacio donde treinta personas ejecutan simultáneamente tareas con perfiles de tráfico distintos: videollamadas, plataformas educativas, descarga de materiales, exámenes en línea y, en paralelo, el docente proyectando contenido. Cuando todos comparten un único medio y ninguna política ordena el acceso, el resultado es predecible: la aplicación más sensible al retardo —la videollamada— se degrada primero, y la más tolerante —la descarga— consume el ancho de banda disponible.

El aula objeto de este diseño presenta esa configuración. Un punto de acceso inalámbrico conectado al router del proveedor, un switch de ocho puertos no administrable y cableado tendido sin canalización ni identificación. La red no distingue usuarios: cualquier dispositivo que conozca la clave accede a todos los recursos, incluida la administración del router.

La pregunta que guía el trabajo es: ¿qué arquitectura de red permite sostener treinta puestos de trabajo con acceso segmentado, calidad de servicio y control, en un aula de dimensiones convencionales y con presupuesto restringido?

Los objetivos específicos son: levantar los requerimientos de usuarios y aplicaciones; definir la topología y el cableado; planificar el direccionamiento y la segmentación lógica; establecer el esquema de seguridad y las políticas de uso; y describir el funcionamiento operativo de la red resultante, con pruebas de aceptación verificables.

## 2. Marco teórico

### 2.1 Modelo de referencia y capas implicadas

El modelo TCP/IP organiza la comunicación en cuatro niveles (Forouzan, 2013; Kurose y Ross, 2017; Tanenbaum y Wetherall, 2012). En el nivel de acceso a la red actúan Ethernet (IEEE 802.3) y Wi-Fi (IEEE 802.11); en el de internet, el protocolo IP con su direccionamiento y enrutamiento; en el de transporte, TCP y UDP; en el de aplicación, HTTP, DNS y los protocolos propios de las plataformas educativas. Esta separación importa porque cada decisión de diseño incide en una capa distinta: el cableado afecta la capa física, la VLAN afecta el nivel de enlace, el direccionamiento afecta la capa de red y la política de calidad afecta el tratamiento de la cola.

### 2.2 Topologías y conmutación

La topología en estrella concentra las conexiones en un dispositivo central que conmuta tramas según la dirección MAC de destino (Cisco Systems, 2020). Su ventaja frente al bus es el aislamiento de fallas: un cable defectuoso afecta un puesto, no al conjunto. La variante jerárquica agrega un nivel de distribución —el switch del aula— y otro de núcleo —el router o firewall—, lo que permite aplicar políticas en el punto adecuado y escalar sin rediseñar.

| Topología | Ventaja | Límite | Idoneidad para el aula |
|---|---|---|---|
| Bus | Bajo costo de cableado | Una falla interrumpe todo el segmento y las colisiones degradan el servicio | Descartada |
| Anillo | Tráfico ordenado y recuperación con doble anillo | Complejidad y costo de interfaces | Descartada |
| Estrella | Falla aislada por puerto y diagnóstico simple | Dependencia del nodo central | Adoptada |
| Malla parcial | Redundancia en enlaces críticos | Costo de puertos y de cableado | Solo si se exige tolerancia a fallas en el enlace principal |

### 2.3 Segmentación lógica

Una VLAN divide un switch físico en dominios de difusión independientes. El estándar IEEE 802.1Q añade una etiqueta de cuatro bytes a la trama para identificar la VLAN en los enlaces troncales. La consecuencia práctica es que dos equipos conectados al mismo switch pueden quedar aislados si pertenecen a VLAN distintas, y el tráfico entre ellas debe pasar por un dispositivo de capa 3 que aplique reglas.

### 2.4 Direccionamiento y servicios

El direccionamiento IPv4 privado definido en el RFC 1918 (Rekhter et al., 1996) permite operar sin depender de bloques públicos. La máscara define el tamaño de la subred y, con ella, el número de hosts utilizables: dos direcciones se reservan para red y difusión. DHCP asigna configuración de forma automática; DNS traduce nombres; NAT permite que múltiples hosts compartan una dirección pública.

### 2.5 Inalámbrico y seguridad

Wi-Fi 6 (802.11ax) mejora la eficiencia espectral en escenarios densos mediante OFDMA y MU-MIMO, pero no elimina la naturaleza compartida del medio: el ancho de banda se distribuye entre los clientes asociados. La seguridad pasa por WPA3, autenticación 802.1X para equipos institucionales y una red separada para invitados. A nivel de infraestructura, resultan pertinentes el filtrado de puertos, la protección contra DHCP no autorizado y el registro de eventos.

| Estándar o norma | Aporte al diseño |
|---|---|
| IEEE 802.3 | Ethernet conmutado en los puestos fijos |
| IEEE 802.1Q | Etiquetado de VLAN en enlaces troncales |
| IEEE 802.11ax | Eficiencia en escenarios densos |
| IEEE 802.1X | Autenticación de equipos docentes |
| ANSI/TIA-568 | Cableado estructurado y categorías |
| ISO/IEC 27001 | Marco de gestión de seguridad de la información |

## 3. Levantamiento de requerimientos

El dimensionamiento parte del uso concurrente, no del número de matrículas.

| Variable | Valor adoptado | Fundamento |
|---|---|---|
| Estudiantes simultáneos | 30 | Capacidad del aula |
| Docentes | 1 | Conducción de la clase |
| Dispositivos por estudiante | 1,2 en promedio | Teléfono y portátil en proporción variable |
| Dispositivos fijos | Proyector, servidor de recursos, cámara | Recursos del aula |
| Ancho de banda por estudiante | 4 Mbps sostenidos | Videoclase en 720p más navegación |
| Ancho de banda del docente | 10 Mbps | Proyección y gestión |
| Demanda agregada estimada | 130 Mbps | Suma de puestos más recursos |
| Disponibilidad objetivo | 99% en horario académico | Continuidad de la clase |
| Latencia objetivo en LAN | Menor a 2 ms | Respuesta de plataformas locales |

La demanda agregada de 130 Mbps no exige un enlace de esa capacidad: exige que el enlace no se sature y que las políticas impidan que un solo equipo consuma la cuota colectiva. Un enlace simétrico de 300 Mbps con calidad de servicio configurada resulta suficiente y deja margen para picos.

## 4. Diseño de la red

### 4.1 Topología

Se adopta una estrella jerárquica de dos niveles. El firewall/router concentra el enlace con el proveedor y aplica las reglas entre segmentos. El switch gestionable de 48 puertos distribuye la conexión a los puestos fijos mediante cableado estructurado y alimenta los puntos de acceso por PoE. Los equipos móviles acceden por dos puntos de acceso Wi-Fi 6 ubicados en extremos opuestos del aula, ambos conectados al switch por enlace Gigabit.

```
                        INTERNET
                            |
                   [ Firewall / Router ]
                    LAN trunk 802.1Q
                            |
              +-------------+-------------+
              |                           |
     [ Switch gestionable 48p ]     [ Servidor local ]
       |        |        |   |
       |        |        |   +--> [ AP Wi-Fi 6 - Norte ] ))) estudiantes
       |        |        +------> [ AP Wi-Fi 6 - Sur   ] ))) docentes/invitados
       |        +---------------> [ Proyector / cámara ]
       +------------------------> 24 rosetas de puestos fijos
```

### 4.2 Cableado y equipamiento

| Elemento | Especificación | Cantidad |
|---|---|---|
| Cable horizontal | UTP Cat 6A, LSZH, tramos menores a 90 m | 3 cajas de 305 m |
| Rosetas | RJ-45 Cat 6A: 24 puestos fijos y 2 en la pared docente | 26 |
| Patch panel | 48 puertos Cat 6A con identificación | 1 |
| Patch cords | Cat 6A, 1 m y 3 m | 40 |
| Switch | 48 puertos Gigabit, 4 SFP, PoE+ con presupuesto de 150 W, administrable | 1 |
| Puntos de acceso | Wi-Fi 6, doble banda, PoE+ (IEEE 802.3at), 2×2 MIMO | 2 |
| Firewall/router | 4 puertos LAN, VPN, control de ancho de banda | 1 |
| Rack | 12U con ventilación y organizador | 1 |
| UPS | 1000 VA, autonomía mínima de 15 min | 1 |
| Canalización | Canaleta Ranurada 40×25 mm y cajas | Según recorrido |

La longitud máxima del enlace horizontal se mantiene por debajo de los 90 metros, con 10 metros adicionales para los latiguillos, conforme al cableado estructurado normalizado (Telecommunications Industry Association, 2015, 2018). Todos los tramos se identifican en ambos extremos con etiqueta coincidente en roseta y patch panel.

El aula dispone de 24 puestos cableados; la diferencia hasta los 30 estudiantes simultáneos se cubre con dispositivos móviles sobre Wi-Fi, decisión coherente con el dimensionamiento por concurrencia y no con la matrícula. La cantidad de cable merece una advertencia: una caja de 305 metros no alcanza para 26 tiradas. Aun con recorridos promedio de 25 metros el consumo ronda los 650, y el desperdicio propio de la instalación —pérdidas en cada terminación, reserva en el rack— eleva la cifra por encima de los 700; el presupuesto prevé por eso tres cajas.

### 4.3 Direccionamiento y VLAN

| VLAN | Nombre | Subred | Máscara | Rango utilizable | Puerta de enlace | Hosts |
|---|---|---|---|---|---|---|
| 10 | Docentes | 192.168.10.0 | /26 | .1 – .62 | 192.168.10.1 | 62 |
| 20 | Estudiantes | 192.168.20.0 | /25 | .1 – .126 | 192.168.20.1 | 126 |
| 30 | Invitados | 192.168.30.0 | /27 | .1 – .30 | 192.168.30.1 | 30 |
| 40 | Gestión | 192.168.40.0 | /28 | .1 – .14 | 192.168.40.1 | 14 |
| 50 | Recursos | 192.168.50.0 | /28 | .1 – .14 | 192.168.50.1 | 14 |

La asignación se realiza por DHCP con reservas para el proyector, el servidor y los puntos de acceso. En cada subred, la primera dirección utilizable queda ocupada por la puerta de enlace, de modo que la capacidad para clientes es de 61, 125, 29, 13 y 13 hosts respectivamente; la diferencia es irrelevante aquí, pero conviene tenerla presente al leer la columna. Los rangos se dimensionan con holgura: la VLAN de estudiantes admite 125 clientes, cuatro veces la matrícula, lo que cubre dispositivos adicionales sin reconfigurar.

### 4.4 Inalámbrico

Se publican tres SSID: `AULA-DOCENTES` con WPA3-Enterprise y 802.1X; `AULA-ESTUDIANTES` con WPA3-Personal y clave rotativa por período académico; `AULA-INVITADOS` con portal cautivo y aislamiento de clientes. En 2,4 GHz se fijan los canales 1, 6 y 11 para evitar solapamiento; en 5 GHz se habilitan canales no DFS de forma preferente y se desactivan las tasas heredadas. La potencia se ajusta para cubrir el aula sin derramar señal hacia pasillos y aulas vecinas, lo que reduce interferencias y limita el acceso desde fuera.

WPA3-Enterprise no funciona por sí sola: el 802.1X exige un servidor de autenticación que valide las credenciales y entregue las claves de sesión. El diseño prevé RADIUS alojado en el servidor de recursos, con certificado propio, de modo que la red docente no dependa de una clave compartida que circula entre el personal. Si ese servicio cae, las estaciones ya asociadas conservan la sesión, pero las nuevas asociaciones fallan; por eso su disponibilidad se incluye en el plan de respaldo y no se trata como un detalle de configuración.

### 4.5 Seguridad y políticas

Las reglas entre segmentos se definen por defecto como denegación, con excepciones explícitas: los docentes acceden al servidor local y a la administración del proyector; los estudiantes acceden a internet y al servidor de recursos en modo lectura; los invitados acceden solo a internet. La VLAN de gestión no es alcanzable desde ningún otro segmento. Se habilitan protección contra DHCP no autorizado, límite de direcciones MAC por puerto, desactivación de puertos sin uso y registro de eventos hacia un colector local.

| Riesgo | Control aplicado |
|---|---|
| Acceso no autorizado a la administración | VLAN separada y regla de denegación explícita |
| Suplantación de servidor DHCP | DHCP snooping y puerto de confianza definido |
| Saturación del enlace | Colas por clase de tráfico y límite por cliente |
| Dispositivo infectado | Segmentación, filtrado DNS y bloqueo por puerto |
| Fuga de información del alumnado | Acceso restringido al servidor y respaldo cifrado |

La política descrita sigue el criterio de denegación por defecto y revisión periódica de reglas recomendado para cortafuegos (National Institute of Standards and Technology, 2009), y se inscribe en un marco de gestión de seguridad de la información (ISO/IEC, 2022). El tratamiento de datos del alumnado y la responsabilidad frente a accesos indebidos tienen además consecuencias jurídicas: la Ley Especial contra los Delitos Informáticos (República Bolivariana de Venezuela, 2001) tipifica el acceso indebido a sistemas y la divulgación de información reservada, lo que obliga a documentar quién accede a los registros y con qué autorización.

## 5. Cómo funciona la red

### 5.1 Secuencia operativa

1. **Arranque del equipo del puesto.** La tarjeta de red negocia velocidad y dúplex con el switch; el puerto se asigna a la VLAN 20 por configuración de acceso.
2. **Solicitud DHCP.** El equipo emite un *DHCP Discover* en difusión, limitado a su VLAN. El servidor responde con una dirección del rango 192.168.20.0/25, máscara, puerta de enlace y servidores DNS.
3. **Resolución de nombres.** Al abrir una plataforma, el equipo consulta al DNS. La consulta se reenvía al resolver configurado en el firewall, que aplica filtrado por categoría.
4. **Acceso al recurso.** Si el destino es interno —el servidor de recursos—, el tráfico se conmuta dentro de la VLAN o cruza al segmento 50 según la regla permitida. Si es externo, el firewall aplica NAT y registra la sesión.
5. **Aplicación de calidad de servicio.** El tráfico de videoconferencia se marca y se coloca en una cola prioritaria; las descargas ocupan la cola de mejor esfuerzo y se limitan por cliente.
6. **Ingreso inalámbrico.** Un dispositivo móvil se asocia al SSID correspondiente, se autentica y recibe direccionamiento de la VLAN asociada al SSID, sin posibilidad de alcanzar la VLAN de gestión.

### 5.2 Por qué este diseño y no otro

La estrella jerárquica se elige porque aísla fallas y permite aplicar políticas en un punto. El cableado Categoría 6A en los puestos fijos responde a una razón simple: el medio guiado ofrece ancho de banda dedicado y latencia estable, condiciones que el inalámbrico comparte entre todos los clientes. Destinar el Wi-Fi a la movilidad —y no a la totalidad del aula— descarga el espectro y mejora la experiencia de quienes sí lo requieren.

La segmentación por VLAN no persigue un fin estético. Sin ella, un equipo comprometido podría intentar alcanzar la administración del switch o el servidor de expedientes. Con ella, el daño potencial queda contenido en el segmento y el tráfico entre áreas se convierte en una decisión explícita.

| Alternativa de separación | Costo | Flexibilidad | Control del tráfico lateral | Valoración |
|---|---|---|---|---|
| Red física independiente por grupo | Alto: un switch y un tendido por segmento | Baja: mover un puesto exige recablear | Alto, por aislamiento físico | Descartada por costo |
| Subredes IP sobre un switch plano | Bajo | Alta | Nulo: nada impide el tránsito entre subredes | Insuficiente |
| VLAN con enrutamiento y firewall | Medio | Alta: el cambio es de configuración | Alto: reglas explícitas por segmento | Adoptada |

La subred /25 para estudiantes, mayor que las demás, refleja la distribución real de la demanda; las subredes /27 y /28 reservan espacio para invitados y gestión sin desperdiciar direcciones.

El doble punto de acceso obedece a la geometría del aula y a la densidad: dos celdas con cobertura parcialmente solapada permiten que treinta dispositivos se repartan, y el roaming entre celdas ocurre sin interrupción perceptible si la potencia y los canales están ajustados. Un solo AP, aun con Wi-Fi 6, concentra asociaciones y aire compartido en un único punto de falla.

### 5.3 Pruebas de aceptación

| Prueba | Criterio | Instrumento |
|---|---|---|
| Cobertura | Señal igual o superior a −67 dBm en todos los puestos | Analizador Wi-Fi |
| Latencia interna | Menor a 2 ms al servidor local | Ping sostenido |
| Rendimiento | Al menos 200 Mbps agregados en 5 GHz | Prueba de throughput |
| Aislamiento | Un equipo de estudiantes no alcanza la VLAN de gestión | Escaneo de puertos |
| DHCP | Ningún cliente recibe dirección de un servidor no autorizado | Registro del switch |
| Conmutación de falla | El aula conserva servicio ante caída de un AP | Prueba de desconexión |

## 6. Limitaciones

El diseño asume que la institución puede ejecutar obra menor para canalizar el cableado; sin esa condición, el tendido quedaría expuesto y vulnerable. La cobertura inalámbrica depende de la densidad de muros y del mobiliario metálico, factores que solo se confirman con medición en sitio. El presupuesto se expresa como lista de materiales y no como cotización: los precios varían por proveedor y por tipo de cambio, de modo que la adquisición requiere consulta formal.

Existe, además, una limitación de gobernanza. La red más robusta fracasa si no se definen responsables: quién administra las credenciales, con qué periodicidad se actualiza el firmware, dónde se almacenan los registros y por cuánto tiempo. La documentación del diseño debe acompañarse de un procedimiento operativo; de lo contrario, la configuración inicial se degrada en pocos meses.

## 7. Conclusiones

La diferencia entre un aula conectada y una red de aula reside en la deliberación. Los componentes propuestos son estándar y ampliamente disponibles; lo que cambia el resultado es la decisión de separar tráficos, dimensionar por concurrencia, priorizar lo sensible al retardo y documentar cada regla. Un diseño así puede auditarse, y esa auditabilidad es la condición para mejorar.

Queda planteada una línea de trabajo pertinente para la formación técnica: evaluar el consumo real de las aplicaciones educativas utilizadas en el aula y ajustar con esos datos las colas de calidad de servicio. El dimensionamiento aquí presentado se apoya en valores de referencia razonables, no en medición local; sustituirlos por evidencia empírica sería el paso siguiente.

## 8. Referencias

Cisco Systems. (2020). *CCNA 200-301 official cert guide* (Vols. 1–2). Cisco Press.

Forouzan, B. A. (2013). *Transmisión de datos y redes de comunicaciones* (5.ª ed.). McGraw-Hill.

IEEE. (2018). *IEEE Standard for Ethernet* (IEEE Std 802.3-2018).

IEEE. (2021). *IEEE Standard for Information Technology—Telecommunications and Information Exchange between Systems—Local and Metropolitan Area Networks—Specific Requirements—Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications* (IEEE Std 802.11-2020).

ISO/IEC. (2022). *ISO/IEC 27001:2022. Information security, cybersecurity and privacy protection — Information security management systems — Requirements*.

Kurose, J. F., y Ross, K. W. (2017). *Redes de computadoras: un enfoque descendente* (7.ª ed.). Pearson Educación.

National Institute of Standards and Technology. (2009). *Guidelines on firewalls and firewall policy* (Special Publication 800-41, Rev. 1).

Rekhter, Y., Moskowitz, B., Karrenberg, D., de Groot, G. J., y Lear, E. (1996). *Address allocation for private internets* (RFC 1918). Internet Engineering Task Force.

República Bolivariana de Venezuela. (2001). *Ley Especial contra los Delitos Informáticos*. Gaceta Oficial N.º 37.313.

Tanenbaum, A. S., y Wetherall, D. J. (2012). *Redes de computadoras* (5.ª ed.). Pearson Educación.

Telecommunications Industry Association. (2015). *ANSI/TIA-568.0-D: Generic telecommunications cabling for customer premises*.

Telecommunications Industry Association. (2018). *ANSI/TIA-568.2-D: Balanced twisted-pair telecommunications cabling and components standard*.

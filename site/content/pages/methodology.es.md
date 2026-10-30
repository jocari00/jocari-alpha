---
title: Metodología
---

## Carteras y decisiones

Hay cinco carteras modelo con un porcentaje fijo de renta variable: Defensive 0 %, Conservative
25 %, Balanced 50 %, Dynamic 75 % y Aggressive 100 %. Los alternativos agresivos cuentan como renta
variable y los defensivos como renta fija. Los pesos objetivo de cada cartera están registrados en el
[repositorio público](https://github.com/jocari00/jocari-alpha/tree/main/decisions) del proyecto.
Cada cambio se registra **antes** de entrar en vigor, de modo que el historial con fechas demuestra
que las decisiones se tomaron sin conocer el resultado.

## Cómo se calculan las rentabilidades

- **Ponderadas en el tiempo, en euros**, a partir del valor liquidativo (VL) de cada fondo. El VL ya
  descuenta los gastos corrientes de los fondos. No se incluyen comisiones de suscripción o
  reembolso ni impuestos.
- **Pesos estáticos.** En cada fecha de valoración la cartera vuelve a sus pesos objetivo, de modo
  que la rentabilidad de un periodo es la media ponderada de la de sus fondos en ese periodo.
- **Fechas de valoración:** 31 de diciembre de 2025 (base 100), 30 de octubre de 2026 y cada fin de
  mes posterior. Cada fondo toma su último VL publicado en los 7 días anteriores a la fecha, lo que
  cubre los festivos y el VL semanal del fondo de bonos catastróficos. Si a una cartera le falta el VL
  de algún fondo, no se valora en esa fecha: los datos que faltan nunca se estiman ni se rellenan.
- **No se anualizan rentabilidades.** Las métricas de riesgo (volatilidad, caída máxima, ratios) se
  añadirán cuando haya al menos doce meses de historial live.

## Periodo estimado y seguimiento live

Las carteras se formalizaron en octubre de 2026. El periodo del 31 de diciembre de 2025 al 30 de
octubre de 2026 es una **estimación**: un único periodo calculado con los pesos objetivo actuales,
que se muestra con línea discontinua y la etiqueta *Estimado*. No es un historial real. El
seguimiento live empieza el 30 de octubre de 2026, con una valoración a cada fin de mes.

## Benchmarks

Cada cartera se compara con una combinación pasiva con su mismo porcentaje de renta variable y
renta fija, construida con ETFs de acumulación cuyo precio ya refleja la rentabilidad total:

- Renta variable: iShares MSCI ACWI UCITS ETF (Acc), con su precio en euros.
- Renta fija: 50 % iShares € Govt Bond 1-3yr UCITS ETF (Acc) y 50 % Vanguard EUR Corporate 1-3 Year
  Bond UCITS ETF (Acc). La renta fija de las carteras es de duración corta, así que compararla con un
  índice agregado de duración larga no sería justo.

| Cartera | MSCI ACWI | Deuda pública EUR 1-3 | Crédito EUR 1-3 |
|---|---|---|---|
| Defensive | 0 % | 50 % | 50 % |
| Conservative | 25 % | 37,5 % | 37,5 % |
| Balanced | 50 % | 25 % | 25 % |
| Dynamic | 75 % | 12,5 % | 12,5 % |
| Aggressive | 100 % | 0 % | 0 % |

Los pesos del benchmark también vuelven a su objetivo en cada fecha de valoración.

## Fuentes de datos

Los VL y los precios de los ETFs se recogen cada semana de las publicaciones de las gestoras y de
otras fuentes públicas, y se contrastan cuando es posible. Solo se publican rentabilidades
combinadas de carteras y benchmarks; no se publican los VL de los fondos.

## Limitaciones

- El periodo estimado usa los pesos actuales y no es un historial real.
- Fondos y ETFs se valoran en momentos distintos y algunos publican con retraso; la ventana de 7 días
  los alinea con cada fecha de valoración, no al mismo minuto.
- Las carteras modelo no son cuentas reales: se ignoran costes de operación, inversiones mínimas e
  impuestos.
- La metodología se inspira en los estándares GIPS®, pero las carteras no cumplen GIPS.

Los gráficos están hechos con [TradingView Lightweight Charts™](https://www.tradingview.com/).

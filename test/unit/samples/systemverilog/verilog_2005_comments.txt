module counter (clk, q);
  input clk;  // clock
  output reg [3:0] q;
  /* count up */
  always @(posedge clk) q <= q + 1;
endmodule

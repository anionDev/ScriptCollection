openssl x509 -req -in CSR.csr -CA MyRootCA.crt -CAkey MyRootCA.key -CAserial MyRootCA.srl -out CSRResult.crt -days 358000 -sha256
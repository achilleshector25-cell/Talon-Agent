"""WASM sandbox — wasmtime based"""
import wasmtime

class WASMSandbox:
    def __init__(self):
        self.engine = wasmtime.Engine()
        self.store = wasmtime.Store(self.engine)
        # WASI with no preopens = no FS access by default
        wasi = wasmtime.WasiConfig()
        wasi.inherit_stdout()
        self.store.set_wasi(wasi)

    def run_wasm(self, wasm_bytes: bytes, func: str = "_start", args: list = []):
        mod = wasmtime.Module(self.engine, wasm_bytes)
        linker = wasmtime.Linker(self.engine)
        linker.define_wasi()
        instance = linker.instantiate(self.store, mod)
        fn = instance.exports(self.store)[func]
        return fn(self.store, *args)
